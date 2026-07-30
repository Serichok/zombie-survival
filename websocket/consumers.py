from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from rooms.models import Room


class RoomConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        self.code = self.scope["url_route"]["kwargs"]["code"].upper()
        if not self.scope["user"].is_authenticated or not await self.is_member():
            await self.close(code=4403); return
        self.group_name = f"room_{self.code}"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, code):
        if hasattr(self, "group_name"): await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive_json(self, content, **kwargs):
        # State changes deliberately go through authenticated REST commands.
        if content.get("type") == "ping": await self.send_json({"type": "pong"})

    async def broadcast(self, event):
        await self.send_json({"type": event["event_type"], "payload": event["payload"]})

    @database_sync_to_async
    def is_member(self): return Room.objects.filter(code=self.code, memberships__user=self.scope["user"]).exists()
