from celery import Celery
import os
from dotenv import load_dotenv

load_dotenv()

# Redis connection URL
REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')

# Create Celery app
celery_app = Celery(
    'resume_processor',
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=['backend.tasks.resume_tasks']
)

# Celery configuration
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=50,
    result_expires=3600,  # 1 hour
)

# Task routing
celery_app.conf.task_routes = {
    'backend.tasks.resume_tasks.*': {'queue': 'resume_processing'},
}

