# api_gateway/consumers.py
from channels.generic.websocket import WebsocketConsumer
from asgiref.sync import async_to_sync
import json

class EventsConsumer(WebsocketConsumer):
    def connect(self):
        # Accept the WebSocket connection
        self.accept()
        # Add this connection to the "events" group
        async_to_sync(self.channel_layer.group_add)("events", self.channel_name)

    def disconnect(self, close_code):
        # Remove from the group on disconnect
        async_to_sync(self.channel_layer.group_discard)("events", self.channel_name)

    def new_event(self, event):
        # This method will be called when `group_send` with type "new_event" is received
        # Send the event data to the WebSocket client
        self.send(text_data=event["event"])
