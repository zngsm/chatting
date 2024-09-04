from django.db import models
from chat_project import settings

# Create your models here.
class ChatRoom(models.Model):
    name = models.fields.CharField(max_length=255)
    last_msg = models.fields.TextField()
    created_at = models.fields.DateTimeField(auto_now=True)
    

class ChatRoomVisit(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='visits')
    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name='visits')
    last_visited_at = models.fields.DateField()
    
    
class Message(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='messages')
    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name='messages')
    content = models.TextField()
    created_at = models.fields.DateTimeField(auto_now=True)