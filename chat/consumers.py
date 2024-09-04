import json
from datetime import datetime, timedelta
from time import timezone
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async


class ChatConsumer(AsyncWebsocketConsumer):
    """
    요구사항
    1. 그룹채팅일 것
    2. 접속시마다 30분내 접속자 수에 포함되어야할 것 -> 이를 클라이언트에 전송할 것
    3. 접속시마다 기존 메시지를 조회할 수 있어야한다.
    """
    async def connect(self):
        pass

    async def disconnect(self, close_code):
        pass

    async def receive(self, text_data):
        pass

