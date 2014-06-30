from datetime import timedelta

BROKER_URL = 'mongodb://localhost:27017/celery_tasks'

CELERY_ACCEPT_CONTENT = ['json', 'pickle']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'

CELERYBEAT_SCHEDULE = {
    'daily_scrapes': {
        'task': 'tasks.scrape_all',
        'schedule': timedelta(hours=12),
        'args': ()
    }
}

CELERY_TIMEZONE = 'UTC'
