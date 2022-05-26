import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))


class Config(object):
    # Storage
    REDIS_URL = os.environ.get("CELERY_BROKER_URL")

    # Deployment settings
    DEBUG = os.environ.get("DEBUG", False)
    PORT = os.environ.get("PORT", 5000)
    # AWS Credentails
    BUCKET_NAME = os.environ.get('BUCKET_NAME')
    AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
    QUEUE_NAME = os.environ.get('QUEUE_NAME')
    MESSAGE_GROUP_ID = os.environ.get('MESSAGE_GROUP_ID')
    AWS_REGION = os.environ.get('AWS_REGION')
    QUEUE_URL = os.environ.get('QUEUE_URL')
