# README

> 실시간 채팅 서비스


- python 3.12
- django (django-rest-framework)
- django channel (with Redis)
- mygsql



## setup

```shell
# 가상환경 설정
$ python -m venv venv

# 패키지 설치
$ pip install -r requirements.txt

# DB, redis 온
$ docker-compose up -d

# start
# 처음 서버 구동시 마이그레이션 과정이 필요합니다.
$ python manage.py migrate

# 서버 on
$ python manage.py runserver
```


## 주요 기능

### HTTP

- 유저 생성
  - POST /accounts
  - ```json
    // body
    {
        "username": "유저 고유 식별 정보",
        "password": "비밀번호",
    }
    ```
- 로그인 API
  - POST /accounts/login
  - ```json
    // body
    {
        "username": "유저 고유 식별 정보",
        "password": "비밀번호",
    }
  
  
  
- 채팅방 개설
  - POST /chat
  - ```json
    // body
    {
      "name": "채팅방 이름",
    }
  
  


### SOCKET

- 채팅방 목록
  - /room/

  - ```json
    // visitor_count 순으로
    {
        "{chatroom.id}": {
            "chatroom_id": chatroom.id,
            "name": chatroom.name,
            "visitor_count": 0,
            "latest_message": {
                "message": message.content,
                "username": user.username,
            },
        },
    }
    ```
  
  - 
  
- 채팅
  - /room/{room_id}/chat/


## 참고사항
- 유저는 굳이 생성하지 않아도 됩니다.(채팅방 입장시 랜덤 유저 생성)


## Code guide
- /accounts : 유저 앱
  - /models.py : 유저 모델 생성
  - /urls.py : 유저 API path
  - /views.py : 유저 API 로직
  - /tests.py : 유저 API 테스트

- /chat : 채팅 앱
  - /models.py : 채팅 관련 모델 생성
  - /urls.py : 채팅 HTTP API path
  - /views.py : 채팅 API 로직
  - /tests.py : 채팅 API 테스트 + 채팅 테스트
  - /routing.py : 채팅 관련 소켓 라우팅
  - /consumers.py : 채팅 관련 소켓 로직
