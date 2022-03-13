import os
import time

from celery import Celery


celery = Celery(__name__)
celery.conf.broker_url = os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379")
celery.conf.result_backend = os.environ.get("CELERY_RESULT_BACKEND", "redis://localhost:6379")
celery.conf.task_serializer = 'pickle'
celery.conf.accept_content = ['application/json','application/x-python-serialize']

@celery.task(name="create_task")
def create_task(task_type,obj=None):
    time.sleep(int(task_type) * 10)
    return True
