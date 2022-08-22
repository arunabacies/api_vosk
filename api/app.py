import celery.states as states
from flask import Flask, Response
from flask import url_for, jsonify
from worker import celery
import json
from config import Config
import boto3

dev_mode = True
app = Flask(__name__)


# @app.route('/add/<int:param1>/<int:param2>')
# def add(param1: int, param2: int) -> str:
#     task = celery.send_task('tasks.add', args=[param1, param2], kwargs={})
#     response = f"<a href='{url_for('check_task', task_id=task.id, external=True)}'>check status of {task.id} </a>"
#     return response
#
#
# @app.route('/check/<string:task_id>')
# def check_task(task_id: str) -> str:
#     res = celery.AsyncResult(task_id)
#     if res.state == states.PENDING:
#         return res.state
#     else:
#         return str(res.result)


@app.route('/health_check')
def health_check() -> Response:
    return jsonify("OK")

@app.route('/get_s3_data',methods=['POST'])
def get_json_data_from_job_id() -> Response:
    try:
        s3 = boto3.client('s3', aws_access_key_id=Config.AWS_ACCESS_KEY_ID,
                        aws_secret_access_key=Config.AWS_SECRET_ACCESS_KEY,
                        region_name=Config.AWS_REGION)
        s3_clientobj = s3.get_object(Bucket=Config.BUCKET_NAME,
                                    Key="credentials/env.json")
        s3_clientdata = s3_clientobj['Body'].read().decode('utf-8')     
    except Exception as e:
        return jsonify({'result': 's3 config error', 'status': 401})
    req_data = json.loads(request.data)
    job_id = req_data.get('job_id')
    try:        
        s3_clientobj = s3.get_object(Bucket=Config.BUCKET_NAME,Key=f"processed/{job_id}.json")
        s3_clientdata = s3_clientobj['Body'].read().decode('utf-8')
        body_is = json.loads(s3_clientdata)
        result = body_is['transcription_results']
        return jsonify({'result': result, 'status': 200})
    except:
        return jsonify({'result': 'None', 'status': 404})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
