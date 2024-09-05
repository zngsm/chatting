from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from chat.serializers import ChatRoomSeriailizer


def _create_chatroom(data):
    serializer = ChatRoomSeriailizer(data=data)
    if serializer.is_valid(raise_exception=True):
        serializer.save()
        return Response(status=status.HTTP_200_OK)


@api_view(["POST"])
def create_chatrooms(request):
    return _create_chatroom(request.data)
