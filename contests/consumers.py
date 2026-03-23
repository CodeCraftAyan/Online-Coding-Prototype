import json
from channels.generic.websocket import AsyncWebsocketConsumer
import asyncio

class VideoConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        await self.channel_layer.group_add("video_group", self.channel_name)
        await self.accept()

        self.keep_alive = True
        asyncio.create_task(self.send_ping())

    async def disconnect(self, close_code):
        self.keep_alive = False
        await self.channel_layer.group_discard("video_group", self.channel_name)

    async def send_ping(self):
        while self.keep_alive:
            await self.send(text_data=json.dumps({"type": "ping"}))
            await asyncio.sleep(20)

    async def send_video_trigger(self, event):
        await self.send(text_data=json.dumps({
            "video_triggered_at": event["video_triggered_at"]
        }))