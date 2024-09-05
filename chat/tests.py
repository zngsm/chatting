from datetime import datetime, timedelta

import pytest
from channels.db import database_sync_to_async
from channels.testing import WebsocketCommunicator
from django.contrib.auth import get_user_model
from django.test import TestCase, TransactionTestCase
from rest_framework import status
from rest_framework.test import APIClient

from chat.const import NO_MSG, SYSTEM
from chat.enums import MessageType
from chat.models import ChatRoom, ChatRoomVisit, Message
from chat_project.asgi import application
from chat_project.helpers import SEOUL_TZ

User = get_user_model()


class TestChatRoom(TestCase):
    def setUp(self):
        self.client = APIClient()

    def _create_user(self, username: str = "Sue"):
        return User.objects.create(username=username, password="1234")

    def _create_chatrooms(self, chatroom_name: str = "자소설 닷컴 채팅방"):
        return ChatRoom.objects.create(name=chatroom_name)

    def _add_user_to_chatroom(self, user, chatroom, last_visited_at):
        return ChatRoomVisit.objects.create(
            user=user, room=chatroom, last_visited_at=last_visited_at
        )

    def test_should_return_recent_visitor_count(self):
        # Given: 유저 생성
        now = datetime.now(tz=SEOUL_TZ)
        user1 = self._create_user()
        user2 = self._create_user("Min")
        user3 = self._create_user("Jang")
        user4 = self._create_user("Zzng")

        # And: 채팅방 생성
        chatroom = self._create_chatrooms()

        # And: user1 한시간 전 방문
        self._add_user_to_chatroom(user1, chatroom, now - timedelta(hours=1))

        # And: user2 20분전 방문
        self._add_user_to_chatroom(user2, chatroom, now - timedelta(minutes=20))

        # And: user3은 미방문, user 4는 현재 방문
        self._add_user_to_chatroom(user4, chatroom, now)

        # When: chatroom 의 recent_visitor_count 호출시
        count = chatroom.recent_visitor_count()

        # Then: 카운트는 user2, user4 두명이어야한다.
        assert count == 2

    def test_should_create_chatroom(self):
        # When: 방 생성 API 요청시
        response = self.client.post("/chat/", data={"name": "자소설 닷컴 채팅방"})

        # Then: 200 OK
        assert response.status_code == status.HTTP_200_OK

        # And: ChatRoom 은 생성데이터와 동일하게 하나 생성되어있다.
        chatrooms = ChatRoom.objects.all()
        assert len(chatrooms) == 1
        assert chatrooms[0].name == "자소설 닷컴 채팅방"

    def test_should_not_create_with_wrong_form(self):
        # When: 잘못된 데이터로 방 생성 API 요청시
        response = self.client.post("/chat/", data={"title": "자소설 닷컴 채팅방"})

        # Then: 400 Bad Request
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.asyncio
class TestSocket(TransactionTestCase):
    async def _create_default_chatroom(self, name: str = "자소설 닷컴"):
        return await database_sync_to_async(ChatRoom.objects.create)(name=name)

    async def _create_default_user(self, name: str = "Sue"):
        return await database_sync_to_async(User.objects.create)(
            username=name, password="!234"
        )

    async def _add_user_to_chatroom(self, user, chatroom, dt):
        return await database_sync_to_async(ChatRoomVisit.objects.create)(
            user=user,
            room=chatroom,
            last_visited_at=dt,
        )

    async def _create_message(self, user, chatroom, content):
        return await database_sync_to_async(Message.objects.create)(
            user=user, room=chatroom, content=content
        )


class TestChat(TestSocket):
    async def test_shold_connect_unauthorized_user(self):
        # Given: 채팅방 생성
        chatroom = await self._create_default_chatroom()

        # When: 유저 없이 comunidcator 객체 생성하여 연결 확인
        communicator = WebsocketCommunicator(application, f"/room/{chatroom.id}/chat/")
        connected, subprotocol = await communicator.connect()

        # Then: 연결은 실패된다.
        assert connected is True

        # And: 유저가 랜덤명으로 생성된다.
        assert await database_sync_to_async(User.objects.exists)()

        # And: WebSocket 연결 종료
        await communicator.disconnect()

    async def test_should_connect_to_chat_room(self):
        # Given: 채팅방 생성
        chatroom = await self._create_default_chatroom()
        user = await self._create_default_user()

        # When: comunidcator 객체 생성하여 연결 확인
        communicator = WebsocketCommunicator(application, f"/room/{chatroom.id}/chat/")
        communicator.scope["user"] = user
        connected, subprotocol = await communicator.connect()

        # Then: 연결은 성공이다.
        assert connected is True
        assert communicator.scope["user"].is_authenticated

        # And: WebSocket 연결 종료
        await communicator.disconnect()

    async def test_should_recode_visit_cnt_when_connect_to_chatroom(self):
        # Given: 채팅방 생성
        now = datetime.now(tz=SEOUL_TZ)
        chatroom = await self._create_default_chatroom()

        # And: 기존 유저 접속 중
        user1 = await self._create_default_user()
        await database_sync_to_async(ChatRoomVisit.objects.create)(
            user=user1, room=chatroom, last_visited_at=now - timedelta(minutes=10)
        )

        # When: 새 유저가 접속
        user2 = await database_sync_to_async(User.objects.create)(
            username="Min", password="!234"
        )
        communicator = WebsocketCommunicator(application, f"/room/{chatroom.id}/chat/")
        communicator.scope["user"] = user2
        await communicator.connect()

        # Then: 유저 카운트를 더해서 응답한다.
        response = await communicator.receive_json_from()
        self._assert_join_msg(response, 2)

        await communicator.disconnect()

        # And: 방문기록이 저장된다.
        assert await database_sync_to_async(
            ChatRoomVisit.objects.filter(user=user2, room=chatroom).exists
        )()

    async def test_should_respond_past_messages_and_visitor_cnt_when_connect_to_chatroom(
        self,
    ):
        # Given: 채팅방 생성
        chatroom = await self._create_default_chatroom()
        user = await self._create_default_user()

        # And: user 접속 후 메시지 생성
        c = WebsocketCommunicator(application, f"/room/{chatroom.id}/chat/")
        c.scope["user"] = user
        await c.connect()

        message1 = await database_sync_to_async(Message.objects.create)(
            user=user, room=chatroom, content="첫번째"
        )
        message2 = await database_sync_to_async(Message.objects.create)(
            user=user, room=chatroom, content="두번째"
        )

        # And: 신규 유저 생성
        user2 = await database_sync_to_async(User.objects.create)(
            username="Min", password="!234"
        )

        # Whem: 연결
        communicator = WebsocketCommunicator(application, f"/room/{chatroom.id}/chat/")
        communicator.scope["user"] = user2
        await communicator.connect()

        # Then:  가장 최신 메시지를 응답합니다.
        response = await communicator.receive_json_from()
        self._assert_message(response, message2, user)

        # And: 그 이전 메시지를 응답합니다.
        response = await communicator.receive_json_from()
        self._assert_message(response, message1, user)

        # And: 현재 접속 인원과 참여 메시지을 응답한다.
        response = await communicator.receive_json_from()
        self._assert_join_msg(response, 2)

        await communicator.disconnect()

    async def test_should_send_and_receive_message(self):
        # Given: 유저 및 채팅방 생성
        user = await self._create_default_user()
        chatroom = await self._create_default_chatroom()

        # And: 인증된 유저로 연결
        communicator = WebsocketCommunicator(application, f"/room/{chatroom.id}/chat/")
        communicator.scope["user"] = user
        connected, subprotocol = await communicator.connect()

        # And: 입장시 메시지 생성
        response = await communicator.receive_json_from()
        self._assert_join_msg(response, 1)

        # When: 메시지를 보낸다.
        message = {"message": "I'm so happy.", "username": user.username}
        await communicator.send_json_to(message)

        # Then: 보낸 메시지와 동일한 메시지를 받는다.
        response = await communicator.receive_json_from()
        assert response["message"] == "I'm so happy."
        assert response["username"] == user.username
        await communicator.disconnect()

        # And: DB에 메시지가 저장된다.
        assert await database_sync_to_async(
            Message.objects.filter(
                user=user, room=chatroom, content="I'm so happy."
            ).exists
        )()

    async def test_should_chat_more_than_two_people(self):
        user1 = await self._create_default_user()
        user2 = await self._create_default_user("Min")
        user3 = await self._create_default_user("Jang")
        chatroom = await self._create_default_chatroom()

        # And: 첫번째 유저 연결
        communicator_1 = WebsocketCommunicator(
            application, f"/room/{chatroom.id}/chat/"
        )
        communicator_1.scope["user"] = user1
        await communicator_1.connect()
        await communicator_1.receive_json_from()  # JOIN MSG

        # And: 두번째 유저 연결
        communicator_2 = WebsocketCommunicator(
            application, f"/room/{chatroom.id}/chat/"
        )
        communicator_2.scope["user"] = user2
        await communicator_2.connect()
        await communicator_1.receive_json_from()  # JOIN MSG
        await communicator_2.receive_json_from()  # JOIN MSG
        # And: 세번째 유저 연결
        communicator_3 = WebsocketCommunicator(
            application, f"/room/{chatroom.id}/chat/"
        )
        communicator_3.scope["user"] = user3
        await communicator_3.connect()
        await communicator_1.receive_json_from()  # JOIN MSG
        await communicator_2.receive_json_from()  # JOIN MSG
        await communicator_3.receive_json_from()  # JOIN MSG

        # When: 첫번째 유저 메시지 전송
        message = {"message": "I'm so happy.", "username": user1.username}
        await communicator_1.send_json_to(message)

        # And: 두번째 유저가 메시지를 받는다.
        response_2 = await communicator_2.receive_json_from()
        assert response_2 == message

        # And: 세번째 유저도 메시지를 받는다.
        response_3 = await communicator_3.receive_json_from()
        assert response_3 == message

    def _assert_message(self, response, message, user):
        assert response["message"] == message.content
        assert response["type"] == MessageType.PAST_MESSAGE
        assert response["username"] == user.username

    def _assert_join_msg(self, response, active_user_cnt):
        assert response["type"] == MessageType.SEND_USER_COUNT
        assert response["active_user_count"] == active_user_cnt


class TestChatRoomInfo(TestSocket):
    async def test_should_respond_chatroom_list_with_latest_msg(self):
        # Given: 챗룸 생성
        chatroom = await self._create_default_chatroom()
        user = await self._create_default_user()

        # And: 메시지 생성
        await database_sync_to_async(Message.objects.create)(
            user=user, room=chatroom, content="첫번째"
        )
        message2 = await database_sync_to_async(Message.objects.create)(
            user=user, room=chatroom, content="두번째"
        )

        # When: 소켓 연결
        communicator = WebsocketCommunicator(application, f"/room/")
        await communicator.connect()

        # Then: 챗룸 정보와 마지막 메시지를 받는다.
        response = await communicator.receive_json_from()
        assert response["results"] == {
            str(chatroom.id): {
                "chatroom_id": chatroom.id,
                "name": chatroom.name,
                "visitor_count": 0,
                "latest_message": {
                    "message": message2.content,
                    "username": user.username,
                },
            }
        }

        # And: 연결 종료
        await communicator.disconnect()

    async def test_should_respond_empty_if_there_is_no_room(self):
        # When: 소켓 연결
        communicator = WebsocketCommunicator(application, f"/room/")
        await communicator.connect()

        # Then: 빈 object 를 응답한다.
        response = await communicator.receive_json_from()
        assert response["results"] == {}

        # And: 연결 종료
        await communicator.disconnect()

    async def test_should_respond_order_by_visitor_count(self):
        # Given: 채팅방 생성
        now = datetime.now(tz=SEOUL_TZ)
        chatroom1 = await self._create_default_chatroom()
        chatroom2 = await self._create_default_chatroom("삼성전자 공채 준비방")
        chatroom3 = await self._create_default_chatroom("롯데그룹 면접방")
        chatroom4 = await self._create_default_chatroom("아무도 없는 방")

        # And: 유저 생성
        user1 = await self._create_default_user()
        user2 = await self._create_default_user("Min")
        user3 = await self._create_default_user("Jang")
        user4 = await self._create_default_user("Zzng")

        # And: chatroom1
        await self._add_user_to_chatroom(user1, chatroom1, now - timedelta(minutes=20))
        await self._add_user_to_chatroom(user2, chatroom1, now - timedelta(minutes=20))
        await self._add_user_to_chatroom(user3, chatroom1, now - timedelta(minutes=20))
        await self._create_message(user1, chatroom1, "반갑습니다.")
        await self._create_message(user2, chatroom1, "저도 반갑습니다.")
        msg_1 = await self._create_message(user3, chatroom1, "하이용")

        # And: chatroom2
        await self._add_user_to_chatroom(user4, chatroom2, now)
        msg_2 = await self._create_message(user4, chatroom2, "방가방가")

        # And: chatroom3 (chatroom4는 아무도 없다.)
        await self._add_user_to_chatroom(user1, chatroom3, now)
        await self._add_user_to_chatroom(user3, chatroom3, now)
        await self._create_message(user1, chatroom3, "안녕하세요.")
        msg_3 = await self._create_message(user3, chatroom3, "반갑습니다.")

        # When: 소켓 연결
        communicator = WebsocketCommunicator(application, f"/room/")
        await communicator.connect()

        # Then: 최근 방문자 수가 많은 순서대로 응답한다.
        response = await communicator.receive_json_from()
        assert response["results"] == {
            str(chatroom1.id): {
                "chatroom_id": chatroom1.id,
                "name": chatroom1.name,
                "visitor_count": 3,
                "latest_message": {
                    "message": msg_1.content,
                    "username": user3.username,
                },
            },
            str(chatroom3.id): {
                "chatroom_id": chatroom3.id,
                "name": chatroom3.name,
                "visitor_count": 2,
                "latest_message": {
                    "message": msg_3.content,
                    "username": user3.username,
                },
            },
            str(chatroom2.id): {
                "chatroom_id": chatroom2.id,
                "name": chatroom2.name,
                "visitor_count": 1,
                "latest_message": {
                    "message": msg_2.content,
                    "username": user4.username,
                },
            },
            str(chatroom4.id): {
                "chatroom_id": chatroom4.id,
                "name": chatroom4.name,
                "visitor_count": 0,
                "latest_message": {"message": NO_MSG, "username": SYSTEM},
            },
        }

    async def test_should_respond_latest_msg_when_msg_is_updated(self):
        # Given: 채팅방 생성 및 메시지
        chatroom = await self._create_default_chatroom()
        user = await self._create_default_user()
        message1 = await database_sync_to_async(Message.objects.create)(
            user=user, room=chatroom, content="첫번째"
        )

        # Whem: 채팅방 정보 소켓 연결
        communicator = WebsocketCommunicator(application, f"/room/")
        connected, subprotocol = await communicator.connect()

        # Then: 최초 메시지를 응답
        response = await communicator.receive_json_from()
        assert response["results"] == {
            str(chatroom.id): {
                "chatroom_id": chatroom.id,
                "name": chatroom.name,
                "visitor_count": 0,
                "latest_message": {
                    "message": message1.content,
                    "username": user.username,
                },
            }
        }

        # And: 새로운 채팅 업데이트
        chat_communicator = WebsocketCommunicator(
            application, f"/room/{chatroom.id}/chat/"
        )
        chat_communicator.scope["user"] = user
        await chat_communicator.connect()

        message = {"message": "I'm so happy.", "username": user.username}
        await chat_communicator.send_json_to(message)

        # Then: 새로 전달된 메시지를 응답한다.
        response = await communicator.receive_json_from()
        assert response["chatroom_id"] == str(chatroom.id)
        assert response["message"] == "I'm so happy."
        assert response["username"] == user.username

        await chat_communicator.disconnect()
        await communicator.disconnect()
