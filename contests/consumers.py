import json
from channels.generic.websocket import AsyncWebsocketConsumer

class VideoConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.channel_layer.group_add("video_group", self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard("video_group", self.channel_name)

    async def send_video_trigger(self, event):
        await self.send(text_data=json.dumps({
            "video_triggered_at": event["video_triggered_at"]
        }))