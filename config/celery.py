# Copyright 2014 MongoDB Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

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

CELERYBEAT_CHDIR="/opt/10gen/search-staging/current"

CELERYBEAT_LOG_FILE="/var/log/10gen/search-staging/celerybeat.log"
#CELERYBEAT_PID_FILE="/var/run/10gen/search-staging/celerybeat.pid"

CELERY_TIMEZONE = 'UTC'
