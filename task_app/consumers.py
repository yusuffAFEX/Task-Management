# your_app/consumers.py

import json
from channels.generic.websocket import AsyncWebsocketConsumer

class TaskConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.channel_layer.group_add("tasks", self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard("tasks", self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        # Process the received data
        await self.channel_layer.group_send(
            "tasks",
            {
                "type": "task_message",
                "message": data
            }
        )

    async def task_message(self, event):
        message = event['message']
        print(message)
        await self.send(text_data=json.dumps(message))
