from datetime import datetime, timedelta

from django.db.models import (CharField, Count, F, OuterRef, Q, Subquery,
                              TextField, Value)
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from chat.enums import HttpMethod
from chat.models import ChatRoom
from chat.serializers import ChatRoomSeriailizer
from chat_project.helpers import SEOUL_TZ


def _create_chatroom(data):
    serializer = ChatRoomSeriailizer(data=data)
    if serializer.is_valid(raise_exception=True):
        serializer.save()
        return Response(status=status.HTTP_200_OK)


@api_view(["POST"])
def create_chatrooms(request):
    return _create_chatroom(request.data)
