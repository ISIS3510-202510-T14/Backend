from django.core.management.base import BaseCommand
from campus_picks.realtime_processor.mongodb_listener import MongoDBChangeListener

class Command(BaseCommand):
    help = 'Starts the MongoDB change stream listener'

    def handle(self, *args, **options):
        self.stdout.write('Starting MongoDB change listener...')
        listener = MongoDBChangeListener()
        listener.start()