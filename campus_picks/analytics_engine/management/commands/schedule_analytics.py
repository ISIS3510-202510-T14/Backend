# analytics_engine/management/commands/schedule_analytics.py
import logging
from django.core.management.base import BaseCommand
from django.conf import settings
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from django_apscheduler.jobstores import DjangoJobStore, register_events
from django_apscheduler.models import DjangoJobExecution

from analytics_engine.views import runDailyAnalytics

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = "Run APScheduler to schedule the daily analytics job at 6pm Colombian time."

    def handle(self, *args, **options):
        scheduler = BlockingScheduler(timezone="America/Bogota")
        scheduler.add_jobstore(DjangoJobStore(), "default")

        # Schedule the daily analytics job at 6 PM
        scheduler.add_job(
            runDailyAnalytics,
            trigger=CronTrigger(hour=18, minute=20),  # 18:00 every day
            id="daily_analytics_job",
            max_instances=1,
            replace_existing=True
        )
        self.stdout.write("Scheduled daily analytics job (ID='daily_analytics') at 18:00 every day.")

        # Add the cleanup job, supplying required max_age
        scheduler.add_job(
            DjangoJobExecution.objects.delete_old_job_executions,
            trigger=CronTrigger(day_of_week="mon", hour=0, minute=0),
            id="cleanup_job_executions",
            replace_existing=True,
            kwargs={"max_age": 604800}  # keep logs for 7 days
        )

        register_events(scheduler)
        self.stdout.write("Analytics Scheduler started. Press Ctrl+C to exit.")

        try:
            scheduler.start()
        except (KeyboardInterrupt, SystemExit):
            self.stdout.write("Analytics Scheduler stopped.")
