import asyncio
from pymongo import MongoClient
from channels.layers import get_channel_layer
from asgiref.sync import sync_to_async

class MongoDBChangeListener:
    def __init__(self):
        self.client = MongoClient('mongodb://localhost:27017/')
        self.db = self.client['your_database']
        self.channel_layer = get_channel_layer()

    async def listen_to_changes(self):
        collection = self.db['events']
        
        # Open change stream
        with collection.watch() as stream:
            while stream.alive:
                try:
                    change = stream.next()
                    
                    # Process only insert and update operations
                    if change['operationType'] in ['insert', 'update']:
                        event_data = change['fullDocument']
                        
                        # Broadcast to all subscribed users
                        # You might want to filter based on user subscriptions
                        await self.channel_layer.group_send(
                            f'events_{event_data.get("user_id", "all")}',
                            {
                                'type': 'push_new_event',
                                'message': event_data
                            }
                        )
                except Exception as e:
                    print(f"Error in change stream: {e}")
                await asyncio.sleep(0.1)  # Prevent tight loop

    def start(self):
        asyncio.run(self.listen_to_changes())

# Run this in a separate process or management command
listener = MongoDBChangeListener()