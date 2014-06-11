from datetime import timedelta

BROKER_URL = 'mongodb://localhost:27017/celery_tasks'

CELERY_ACCEPT_CONTENT = ['json', 'pickle']
CELERY_TASK_SERIALIZER = 'pickle'
CELERY_RESULT_SERIALIZER = 'pickle'

CELERYBEAT_SCHEDULE = {
    'run-scrape': {
        'task': 'tasks.scrapeall',
        'schedule': timedelta(hours=12),
        'args': ()
    }
}
