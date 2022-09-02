import celery.states as states
from flask import Flask, Response
from flask import url_for, jsonify, request
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


@app.route('/get_data_for_job_id', methods=['GET'])
def get_json_data_from_job_id() -> Response:
    try:
        s3_client = boto3.client('s3', aws_access_key_id=Config.AWS_ACCESS_KEY_ID,
                                 aws_secret_access_key=Config.AWS_SECRET_ACCESS_KEY,
                                 region_name=Config.AWS_REGION)
        s3_client_obj = s3_client.get_object(Bucket=Config.BUCKET_NAME, Key=f"processed/{request.args['job_id']}.json")
        result = json.loads(s3_client_obj['Body'].read().decode('utf-8')).get('transcription_results')
        return jsonify({'data': result, 'message': 'Success', 'status': 200})
    except Exception as e:
        return jsonify({'message': 'No Data found', 'status': 404})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
