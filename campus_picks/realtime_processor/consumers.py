from channels.generic.websocket import AsyncWebsocketConsumer
import json
from pymongo import MongoClient
import asyncio

class EventConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user_id = self.scope['url_route']['kwargs']['user_id']
        self.group_name = f'events_{self.user_id}'
        
        # Join channel group
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        await self.accept()
        
        # Start MongoDB change stream listener if not already running
        if not hasattr(self, 'change_stream_task'):
            self.change_stream_task = asyncio.create_task(self.watch_mongodb_changes())

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        # Handle subscription parameters if sent by client
        data = json.loads(text_data)
        # You could store filters or process them here
        
    async def push_event(self, event):
        # Send event to WebSocket client
        await self.send(text_data=json.dumps({
            'type': 'new_event',
            'event_data': event['message']
        }))

    async def watch_mongodb_changes(self):
        client = MongoClient('mongodb://localhost:27017/')
        db = client['your_database']
        collection = db['events']
        
        try:
            async with collection.watch() as stream:
                async for change in stream:
                    # Process change document
                    if change['operationType'] in ['insert', 'update']:
                        event_data = change['fullDocument']
                        # Broadcast to group
                        await self.channel_layer.group_send(
                            self.group_name,
                            {
                                'type': 'push_event',
                                'message': event_data
                            }
                        )
        except Exception as e:
            print(f"Error in change stream: {e}")