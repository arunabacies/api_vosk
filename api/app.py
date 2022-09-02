import celery.states as states
from flask import Flask, Response
from flask import url_for, jsonify, request
from worker import celery
import json
from config import Config
import boto3

dev_mode = True
app = Flask(__name__)


@app.route('/health_check')
def health_check() -> Response:
    return jsonify("OK")


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
