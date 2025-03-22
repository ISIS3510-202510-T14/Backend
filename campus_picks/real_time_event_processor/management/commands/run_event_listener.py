# real_time_event_processor/management/commands/run_event_listener.py
from django.core.management.base import BaseCommand
from django.conf import settings
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
import pymongo, json, logging

class Command(BaseCommand):
    help = "Run MongoDB change stream listener for new events"

    def handle(self, *args, **options):
        # Connect to MongoDB (use settings or environment for the connection string)
        mongo_uri = getattr(settings, "MONGODB_URI", "mongodb://localhost:27017/?replicaSet=rs0")  # example
        client = pymongo.MongoClient(mongo_uri)
        db_name = getattr(settings, "MONGODB_NAME", "your_db_name")
        db = client[db_name]
        events_coll = db["events"]

        # Set up change stream on the "events" collection to listen for new inserts
        try:
            print("Starting MongoDB change stream listener...")
            change_stream = events_coll.watch([{"$match": {"operationType": "insert"}}])
        except Exception as e:
            logging.error(f"Failed to start change stream: {e}")
            return

        channel_layer = get_channel_layer()
        # Iterate over the change stream indefinitely
        for change in change_stream:
            try:
                # Extract the new event document (fullDocument contains the inserted document)
                new_event = change.get("fullDocument")
                if not new_event:
                    continue
                # Broadcast the event to WebSocket group "events"
                async_to_sync(channel_layer.group_send)(
                    "events",  # group name for all event subscribers
                    {
                        "type": "new_event",       # custom event type for consumers
                        "event": json.dumps(new_event, default=str)  # serialize event data
                    }
                )
                # (The consumer will have a method `new_event` to handle this)
                logging.info(f"Broadcasted new event: {new_event}")
            except Exception as e:
                logging.error(f"Error processing change stream event: {e}")
                # If needed, add handling to reconnect or break out of loop on fatal error.
                continue
