from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

app = Celery('core')

app.config_from_object('django.conf:settings', namespace='CELERY')
app.conf.task_acks_late = True
app.conf.worker_prefetch_multiplier = 1
app.conf.broker_connection_retry_on_startup = True
app.autodiscover_tasks()

CELERY_BROKER_URL = 'amqp://guest:guest@rabbitmq//'

app.conf.beat_schedule = {
    'send-open-status-emails-daily': {
        'task': 'apps.tables.tasks.send_open_status_emails',
        'schedule': crontab(hour=6, minute=0),
    },
    "generate_missing_hashes_every_5_minutes": {
        "task": "loader.models.generate_missing_hashes",
        "schedule": 300.0,
    },
    "check_chart_export_every_minute": {
        "task": "apps.tables.charts.charts_views.run_scheduled_chart_exports",
        "schedule": 60.0,
    },
}
