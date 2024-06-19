"""
Expose applications (api and celery worker) to WSGI, used by docker-compose.yaml and uwsgi.yaml
"""

import app
import app_celery

app = app.app
worker = app_celery.app
