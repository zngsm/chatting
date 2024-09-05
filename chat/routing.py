from django.urls import re_path

from chat import consumers

websocket_urlpatterns = [
    re_path(r"^room/$", consumers.ChatRoomConsumer.as_asgi()),
    re_path(r"^room/(?P<room_id>\d+)/chat/$", consumers.ChatConsumer.as_asgi()),
]
