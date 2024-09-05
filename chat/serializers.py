from rest_framework import serializers

from chat.models import ChatRoom


class ChatRoomSeriailizer(serializers.ModelSerializer):

    class Meta:
        model = ChatRoom
        fields = ["name", "id"]
        read_only_fields = ("id",)
