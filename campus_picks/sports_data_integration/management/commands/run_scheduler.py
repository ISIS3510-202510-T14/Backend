# sports_data_integration/management/commands/run_scheduler.py
from django.core.management.base import BaseCommand
from apscheduler.schedulers.blocking import BlockingScheduler
from sports_data_integration.views import poll_events_task

class Command(BaseCommand):
    help = "Run APScheduler to execute periodic tasks."

    def handle(self, *args, **kwargs):
        scheduler = BlockingScheduler()
        # Programa la tarea para que se ejecute cada minuto
        scheduler.add_job(poll_events_task, 'interval', minutes=1)
        self.stdout.write("Scheduler started. Press Ctrl+C to exit.")
        try:
            scheduler.start()
        except (KeyboardInterrupt, SystemExit):
            self.stdout.write("Scheduler stopped.")
