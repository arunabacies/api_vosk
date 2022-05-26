# ATI VOSK PROCESSOR
A speech recognition app which converts audio in the video file to text. The app queries messages from AWS SQS Queue and process the message to perform following actions
- Download video file
- Read audio from video using FFMPEG
- Speech Recognition using VOSK Model
- Save processed data to S3 Bucket
- Send response to URL provided in the SQS Message

## Setting up Environment
The `.env` or `.envDev` file is used to define enviroment variables which will be used run the application. Please setup an AWS account and update the following variables in `.env` or  `.envDev` file.
- AWS_ACCESS_KEY_ID
- AWS_SECRET_ACCESS_KEY
- QUEUE_NAME
- QUEUE_URL
- AWS_REGION
- BUCKET_NAME

**Other Configs**
If you wish to connect the application to an external `REDIS` Instacnce
- CELERY
    - Update `CELERY_BROKER_URL, CELERY_RESULT_BACKEND` in `.env` file   

#### Downloading VOSK Model
1. Download the model file from  [here](https://alphacephei.com/vosk/models). You can also download the same using CLI.

    ```
    wget https://alphacephei.com/vosk/models/vosk-model-en-us-0.22.zip
    ```
2. Unzip the downloaded file & Copy the directory to `./celery-queue` and rename the folder as `model`

## Development Guidelines
We use `.envDev` file for local development. Update development environment variables in  `./.envDev` and  `./celery-queue/.envDev`
### `Install Dependencies`
Create a virtual environment and then install the required dependencies by running
```
cd celery-queue
pip install -r requirements.txt
pip install -r requirements.celery_monitor.txt
```
### `Development`
Please ensure a `Redis` instance is up and running. You can easily setup Redis instance using docker.
```
docker-compose -f docker-compose.development.yml up -d redis
```
Code should be updated or modified in `celery-queue/tasks.py` file. After the the modification you can test the app by running the following commands
```
cd celery-queue
celery -A tasks worker -B --concurrency=2
OR
docker-compose -f docker-compose.development.yml up --build docker-compose.development.yml
```

A graphical Interface for monitoring celery is provided as part of this application `Flower`. The app is linked to potrt `5555`. Goto `http://localhost:5555` after running the follwing command.
```
docker-compose -f docker-compose.development.yml up monitor
```
### `start`

```
docker-compose -f docker-compose.development.yml up
# or
docker-compose -f docker-compose.development.yml up -d   ##(Detached Mode)
```

### `build`

```
docker-compose -f docker-compose.development.yml build
# or
docker-compose -f docker-compose.development.yml build [APP_NAME]    ## worker/monitor/redis/web
```

## Deployment
### `Docker Deployment`
#### Build Image
      docker-compose build


#### Run the app

    docker-compose up -d

The app runs on  port `5001`, environmet variables in the `.env file`.
Lookup `docker-compose.yaml` & `./celery-queue/Dockerfile` file to change docker configuration.
