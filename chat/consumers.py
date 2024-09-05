import json
import uuid
from collections import OrderedDict
from datetime import datetime, timedelta

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth import get_user_model
from django.db.models import (CharField, Count, F, OuterRef, Q, Subquery,
                              TextField, Value)
from django.db.models.functions import Coalesce

from chat.const import (JOIN_MSG, LEAVE_MSG, NO_MSG, SYSTEM,
                        UNAUTHORIZED_ERROR, WEBSOCKET_ERROR)
from chat.enums import MessageType
from chat.models import ChatRoom, ChatRoomVisit, Message
from chat_project.helpers import SEOUL_TZ, datetime_to_str

User = get_user_model()


class ChatRoomConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_group_name = "chatroom"

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self._send_chatroom_list()
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def _send_latest_msg(self):
        last_messages = await self.get_latest_message()
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": MessageType.SEND_CHATROOM_LIST,
                "last_messages": last_messages,
            },
        )

    async def update_latest_msg(self, event):
        await self.send(
            text_data=json.dumps(
                {
                    "type": MessageType.UPDATE_LATEST_MSG,
                    "message": event["message"],
                    "username": event["username"],
                    "chatroom_id": event["chatroom_id"],
                }
            )
        )

    async def _send_chatroom_list(self):
        now = datetime.now(tz=SEOUL_TZ)
        chatrooms = await database_sync_to_async(
            lambda: list(
                ChatRoom.objects.annotate(
                    recent_visitors_count=Count(
                        "visits",
                        filter=Q(
                            visits__last_visited_at__gte=now - timedelta(minutes=30)
                        ),
                    )
                )
                .order_by("-recent_visitors_count")
                .values_list("id", "name", "recent_visitors_count")
            )
        )()
        latest_message = await self.get_latest_message()
        results = OrderedDict(
            (
                str(id_),
                {
                    "chatroom_id": id_,
                    "name": name,
                    "visitor_count": visitor_count,
                    "lastest_message": latest_message.get(id_),
                },
            )
            for id_, name, visitor_count in chatrooms
        )
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": MessageType.SEND_CHATROOM_LIST,
                "results": results,
            },
        )

    async def send_chatroom_list(self, event):
        await self.send(
            text_data=json.dumps(
                {
                    "type": MessageType.SEND_CHATROOM_LIST,
                    "results": event["results"],
                }
            )
        )

    async def get_latest_message(self):
        latest_message_subquery = (
            Message.objects.filter(room=OuterRef("id"))
            .order_by("-created_at")
            .annotate(username=F("user__username"))
            .values("content", "username")[:1]
        )

        latest_messages = await database_sync_to_async(
            lambda: list(
                ChatRoom.objects.annotate(
                    chatroom_id=F("id"),
                    message=Coalesce(
                        Subquery(latest_message_subquery.values("content")),
                        Value(NO_MSG),
                        output_field=TextField(),
                    ),
                    username=Coalesce(
                        Subquery(latest_message_subquery.values("username")),
                        Value(SYSTEM),
                        output_field=CharField(),
                    ),
                ).values_list("id", "message", "username")
            )
        )()
        return {
            id_: {
                "message": msg,
                "username": user,
            }
            for id_, msg, user in latest_messages
        }


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        try:
            self.room_id = self.scope["url_route"]["kwargs"]["room_id"]
            self.room_group_name = f"chat_{self.room_id}"
            self.user = self.scope["user"]
            self.room = await database_sync_to_async(ChatRoom.objects.get)(
                id=self.room_id
            )
            self.user = await self._get_user()

            await self.channel_layer.group_add(self.room_group_name, self.channel_name)
            await self.accept()

            now = datetime.now(tz=SEOUL_TZ)
            await self._record_visit(now)
            await self._send_past_messages()
            await self._send_user_count()

        except Exception as e:
            print(f"{WEBSOCKET_ERROR} {str(e)}")
            await self.close()

    async def _get_user(self):
        if "user" not in self.scope or not self.user.is_authenticated:
            return await self._create_temp_user()
        else:
            return self.scope["user"]

    def generate_unique_id(self):
        return str(uuid.uuid4())[:8]

    async def _create_temp_user(self):
        return await database_sync_to_async(User.objects.create)(
            username=f"{self.generate_unique_id()}", password="1234"
        )

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        message = data["message"]
        await self._save_and_send_chat_msg(message)
        await self._send_latest_message_for_chatroom(message)

    async def chat_message(self, event):
        await self.send(
            text_data=json.dumps(
                {
                    "message": event["message"],
                    "username": event["username"],
                }
            )
        )

    async def _send_user_count(self):
        active_user_count = await database_sync_to_async(
            self.room.recent_visitor_count
        )()
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "active_user_cnt": active_user_count,
                "type": MessageType.SEND_USER_COUNT,
            },
        )

    async def _save_and_send_chat_msg(self, message):
        await database_sync_to_async(Message.objects.create)(
            content=message, room=self.room, user=self.user
        )
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": MessageType.CHAT_MESSAGE,
                "message": message,
                "username": self.user.username,
            },
        )

    async def _record_visit(self, now: datetime):
        return await database_sync_to_async(ChatRoomVisit.objects.create)(
            user=self.user, room=self.room, last_visited_at=now
        )

    async def send_user_count(self, event):
        await self.send(
            text_data=json.dumps(
                {
                    "type": MessageType.SEND_USER_COUNT,
                    "active_user_count": event["active_user_cnt"],
                }
            )
        )

    async def _send_past_messages(self):
        past_messages = await database_sync_to_async(
            lambda: list(
                Message.objects.filter(room=self.room)
                .order_by("-id")
                .select_related("user")
            )
        )()
        for message in past_messages:
            await self.send(
                text_data=json.dumps(
                    {
                        "type": MessageType.PAST_MESSAGE,
                        "message": message.content,
                        "username": message.user.username,
                    }
                )
            )

    async def _send_latest_message_for_chatroom(self, message):
        await self.channel_layer.group_send(
            "chatroom",
            {
                "type": MessageType.UPDATE_LATEST_MSG,
                "message": message,
                "username": self.user.username,
                "chatroom_id": self.room_id,
            },
        )
