import json
import asyncio
from channels.generic.websocket import AsyncWebsocketConsumer


class VideoConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        try:
            # Join group FIRST
            await self.channel_layer.group_add("video_group", self.channel_name)

            # Accept connection ONCE
            await self.accept()
            print("✅ WebSocket connected")

            self.keep_alive = True
            asyncio.create_task(self.send_ping())

        except Exception as e:
            print("❌ Connect error:", e)

    async def disconnect(self, close_code):
        print(f"❌ WebSocket disconnected (code: {close_code})")

        self.keep_alive = False

        try:
            await self.channel_layer.group_discard("video_group", self.channel_name)
        except Exception as e:
            print("❌ Disconnect error:", e)

    async def send_ping(self):
        try:
            while self.keep_alive:
                await self.send(text_data=json.dumps({"type": "ping"}))
                await asyncio.sleep(20)
        except Exception as e:
            print("❌ Ping error:", e)

    async def send_video_trigger(self, event):
        try:
            await self.send(text_data=json.dumps({
                "video_triggered_at": event["video_triggered_at"]
            }))
        except Exception as e:
            print("❌ Send video error:", e)
