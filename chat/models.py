from datetime import datetime, timedelta

from django.db import models

from chat_project import settings
from chat_project.helpers import SEOUL_TZ


# Create your models here.
class ChatRoom(models.Model):
    name = models.fields.CharField(max_length=255)
    created_at = models.fields.DateTimeField(auto_now=True)

    def recent_visitor_count(self):
        now = datetime.now(tz=SEOUL_TZ)
        return ChatRoomVisit.objects.filter(
            room=self, last_visited_at__gte=now - timedelta(minutes=30)
        ).count()


class ChatRoomVisit(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="visits"
    )
    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name="visits")
    last_visited_at = models.fields.DateTimeField(null=True, db_index=True)

    def active_users(cls, room, minutes: int = 30):
        return cls.objects.filter(
            room=room,
            last_visited_at__gte=datetime.now(tz=SEOUL_TZ) - timedelta(minutes=minutes),
        ).count()


class Message(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="messages"
    )
    room = models.ForeignKey(
        ChatRoom, on_delete=models.CASCADE, related_name="messages"
    )
    content = models.TextField()
    created_at = models.fields.DateTimeField(auto_now=True, db_index=True)
