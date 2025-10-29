import shlex
import subprocess
import sys
import time
import os
from django.core.management.base import BaseCommand
from django.utils.autoreload import run_with_reloader

class Command(BaseCommand):
    help = "Run both Celery worker and Celery Beat together with auto-reload"

    def stop_existing_celery(self):
        """Stop any running Celery workers."""
        if sys.platform == "win32":
            stop_cmd = "taskkill /f /t /im celery.exe"
        else:
            stop_cmd = "pkill -9 -f 'celery -A core worker'"
        
        subprocess.call(shlex.split(stop_cmd), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    def start_celery(self):
        """Start Celery worker and Celery beat."""
        self.stdout.write(self.style.SUCCESS("Starting Celery Worker and Beat..."))

        # Start Celery Worker
        worker_cmd = [
            "celery", "-A", "core", "worker",
            "--loglevel=info", "--pool=threads",
            "--concurrency=2", "--time-limit=300",
            "--soft-time-limit=240"
        ]
        self.worker_process = subprocess.Popen(worker_cmd, stdout=sys.stdout, stderr=sys.stderr)

        time.sleep(5)

        # Start Celery Beat
        beat_cmd = [
            "celery", "-A", "core", "beat",
            "--loglevel=debug",
            "--scheduler", "django_celery_beat.schedulers:DatabaseScheduler"
        ]
        self.beat_process = subprocess.Popen(beat_cmd, stdout=sys.stdout, stderr=sys.stderr)

        try:
            self.worker_process.wait()
            self.beat_process.wait()
        except KeyboardInterrupt:
            self.stop_celery()

    def stop_celery(self):
        """Terminate Celery Worker and Beat."""
        self.stdout.write(self.style.WARNING("Stopping Celery Worker and Beat..."))
        self.worker_process.terminate()
        self.beat_process.terminate()
        time.sleep(2)

    def handle(self, *args, **kwargs):
        """Main command execution."""
        self.stop_existing_celery()
        run_with_reloader(self.start_celery)