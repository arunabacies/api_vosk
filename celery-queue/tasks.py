from datetime import timedelta
from celery import Celery
from celery.exceptions import SoftTimeLimitExceeded
from config import Config
import json
import os
import shlex
import subprocess
import requests
import time
import boto3
from botocore.errorfactory import ClientError
from vosk import Model, KaldiRecognizer, SetLogLevel
import psutil
from requests.exceptions import ConnectionError

app = Celery('tasks', broker=Config.REDIS_URL,  backend=Config.REDIS_URL)
app.conf.timezone = 'UTC'
app.conf.beat_schedule = {
    'add-every-1-minute': {
        'task': 'tasks.start_processing',
        'schedule': timedelta(seconds=60),
        'options': {
            'expires': 20.0,
        }
    },
}

if not os.path.exists("model"):
    print(
        "Please download the model from https://alphacephei.com/vosk/models and unpack as 'model' in the current folder.")
    exit(1)

sample_rate = 16000
model = Model("model")

# Load Env From S3 BUCKET
try:
    s3 = boto3.client('s3', aws_access_key_id=Config.AWS_ACCESS_KEY_ID,
                      aws_secret_access_key=Config.AWS_SECRET_ACCESS_KEY,
                      region_name=Config.AWS_REGION)
    s3_clientobj = s3.get_object(Bucket=Config.BUCKET_NAME,
                                 Key="credentials/env.json")
    s3_clientdata = s3_clientobj['Body'].read().decode('utf-8')
    CONFIG_FROM_S3 = json.loads(s3_clientdata)
    print("CONFIG_FROM_S3::::")
except Exception as e:
    CONFIG_FROM_S3 = {}


def webhook_sending(body_is: dict) -> bool:
    """Send payload to a Hook URL."""
    attempt = 0
    payload = body_is
    while attempt <= 4:
        attempt += 1
        try:
            response = requests.post(body_is['webhook_url'], json=payload)
            if response.status_code == 200:
                return True
        except ConnectionError as e:
            continue
        # print(response)
    return True


def get_sec(time_str):
    """Get seconds from time."""
    h, m, s = time_str.split(':')
    return int(h) * 3600 + int(m) * 60 + int(s)


@app.task
def download_file(body_is: dict, receipt_handle: str) -> bool:
    data = {}
    try:
        # Download File to Local storage
        start_time = time.time()
        os.system(
            f"wget -O tmp/{body_is['job_id']} {body_is['file_to_transcribe']}")
        file_size = os.stat(f"tmp/{body_is['job_id']}")  # get the file size
        data['download_time_in_seconds'] = float(
            "{:.2f}".format(time.time() - start_time))
        data['file_size_in_mb'] = float(f'{file_size.st_size / 1000000:.2f}')
        data['file_downloaded'] = True

        # Get Media File Details from FFMPEG
        ffmpeg_cmd = "ffmpeg -i ./tmp/{file} -f null -".format(
            file=body_is["job_id"])
        command1 = shlex.split(ffmpeg_cmd)
        video_stats = subprocess.Popen(
            command1, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE).communicate()
        file_duration = None
        max_time_factor = int(CONFIG_FROM_S3.get('maxTimeFactor', 8))
        stats_data = video_stats[1].decode("utf-8").split()
        for index, item in enumerate(stats_data):
            # Get File Duration
            if 'Duration' in item:
                file_duration = float(
                    f'{get_sec(stats_data[index + 1].split(".")[0])}.{stats_data[index + 1].split(".")[1][:-1]}')
                data['file_duration_in_seconds'] = file_duration
            if 'Hz,' in item :
                print("GOT IT::::")
                data['sample_rate'] = int(stats_data[index-1])

        # Update the payload
        body_is.update(data)

        # Create ML processing task
        if file_duration is None:
            ffmpeg_process.apply_async(
                args=(body_is, receipt_handle), soft_time_limit=900)
        else:
            print("FILE_DURATION, TIME_LIMIT:::: {} {} {}".format(
                file_duration,
                int(file_duration) * max_time_factor,
                max_time_factor
            ))
            max_time_limit = int(file_duration) * max_time_factor
            ffmpeg_process.apply_async(
                args=(body_is, receipt_handle),
                soft_time_limit=max_time_limit)

    except Exception as e:
        print(f'File could not be downloaded, error occurred is {e}')

    return True


@app.task
def ffmpeg_process(body_is: dict, receipt_handle: str) -> tuple:
    """
    Read the video file using ffmpeg
    """
    try:
        start_time = time.time()
        audio_sample_rate = body_is.get('sample_rate', sample_rate)
        print("FFMPEG & VOSK :::: sample_rate {}".format(audio_sample_rate))
        process = subprocess.Popen(
            ['ffmpeg', '-loglevel', 'quiet', '-i', f'./tmp/{body_is["job_id"]}', '-ar', str(audio_sample_rate), '-ac', '1', '-f',
             's16le', '-'], stdout=subprocess.PIPE)

        output_text = ""
        rec = KaldiRecognizer(model, sample_rate)
        while True:
            data = process.stdout.read(4000)
            if len(data) != 0 and rec.AcceptWaveform(data):
                fetched = json.loads(rec.Result()).get('text')
                if fetched:
                    output_text = f"{output_text} {fetched}"
            elif len(data) == 0:
                break
        fetched = json.loads(rec.FinalResult()).get('text')
        output_text = f'{output_text} {fetched}'
        body_is.update({
            'vosk_processing_time_in_seconds': float("{:.2f}".format(time.time() - start_time)),
            'vosk_processing_timestamp_finished': time.time(),
            'vosk_processing_timestamp_started': start_time,
            'transcription_results': {'audio_text': output_text.strip()},
            'ffmpeg_processed': True
        })

        finishing.delay(body_is, receipt_handle)
    except SoftTimeLimitExceeded:
        body_is.update({
            'ffmpeg_processed': False,
            'message': 'Process Timeout!'
        })
        finishing.delay(body_is, receipt_handle)
    return True


@app.task
def finishing(body_is: dict, receipt_handle: str):
    print("FINISHING::::", body_is['job_id'])
    try:
        # Delete the processed video file
        os.remove(f"./tmp/{body_is['job_id']}")
    except OSError:
        pass
    # delete from message queue
    sqs = boto3.client('sqs', aws_access_key_id=Config.AWS_ACCESS_KEY_ID,
                       aws_secret_access_key=Config.AWS_SECRET_ACCESS_KEY,
                       region_name=Config.AWS_REGION)
    try:
        s3 = boto3.client('s3', aws_access_key_id=Config.AWS_ACCESS_KEY_ID,
                          aws_secret_access_key=Config.AWS_SECRET_ACCESS_KEY,
                          region_name=Config.AWS_REGION)

        s3.head_object(Bucket=Config.BUCKET_NAME,
                       Key=f"processed/{body_is['job_id']}.json")

    except ClientError:
        print("S3 UPLOAD:::")
        # s3.put_object(Body=json.dumps(body_is),
        #               Bucket=Config.BUCKET_NAME, Key=f"processed/{body_is['job_id']}.json")

    sqs.delete_message(QueueUrl=Config.QUEUE_URL,
                       ReceiptHandle=receipt_handle)
    webhook_sending(body_is)
    return True


@app.task
def start_processing():
    print("RUNNING SCHEDULER::::")
    if psutil.cpu_percent(interval=10) > 80.0:
        print("SKIP::::")
        return False

    sqs = boto3.client('sqs', aws_access_key_id=Config.AWS_ACCESS_KEY_ID,
                       aws_secret_access_key=Config.AWS_SECRET_ACCESS_KEY,
                       region_name=Config.AWS_REGION)
    s3 = boto3.client('s3', aws_access_key_id=Config.AWS_ACCESS_KEY_ID,
                      aws_secret_access_key=Config.AWS_SECRET_ACCESS_KEY,
                      region_name=Config.AWS_REGION)
    response = sqs.receive_message(
        QueueUrl=Config.QUEUE_URL,
        MaxNumberOfMessages=10,
        MessageAttributeNames=['All'],
        WaitTimeSeconds=20
    )
    for msg in response.get('Messages', []):
        # if Job ID Exists return results else download file
        payload = json.loads(msg.get('Body', {}))
        try:
            s3.head_object(Bucket=Config.BUCKET_NAME,
                           Key=f"processed/{payload['job_id']}.json")
            s3_clientobj = s3.get_object(Bucket=Config.BUCKET_NAME,
                                         Key=f"processed/{payload['job_id']}.json")
            s3_clientdata = s3_clientobj['Body'].read().decode('utf-8')
            body_is = json.loads(s3_clientdata)
            print("CHECK PASS:::")
            finishing.delay(body_is,  msg['ReceiptHandle'])

        except ClientError:
            download_file.delay(payload, msg['ReceiptHandle'])

    return True
