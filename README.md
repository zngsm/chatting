# README

> 실시간 채팅 서비스



- python 3.12
- django (django-rest-framework)
- channel





## setup

```shell
# 가상환경 설정
$ python -m venv venv

# 패키지 설치
$ pip install -r requirements.txt

# DB, redis 온
$ docker-compose up -d

# start
$ python manage.py migrate

$ python manage.py runserver
```





## ERD







## API

- 유저 생성 API
  - POST /user
  - ```json
    // body
    {
        "name": "유저 고유 식별 정보",
    }
    ```

- 채팅방 생성 API

  - POST /chat

  - ```json
    // body
    {
        "user_name": "유저 고유식별정보",
        "title": "채팅방 제목",
    }
    ```

    - 방장의 개념은 없기 때문에, 생성한 유저도 유저리스트의 일부로 들어간다.

- 채팅방 조회 API

  - GET /chat

  - ```json
    // Response
    {
        "results": [
            {"id": "채팅방 아이디", "title": "채팅방 제목", "user_count": "30분간 유저 카운트"},
            {"id": "채팅방 아이디", "title": "채팅방 제목", "user_count": "30분간 유저 카운트"},
            {"id": "채팅방 아이디", "title": "채팅방 제목", "user_count": "30분간 유저 카운트"},
            ...
        ]
    }
    ```

    - 채팅방 제목이 unique 하지 않기 때문에 제목을 같이 넣어준다.

- 실시간 채팅 API

  - POST /chat/{room_id}

  - ```json
    // body
    {
        "user_name": "유저 고유 식별 정보",
        "content": "채팅 내용",
    }
    ```

- 채팅 목록 조회 API

  - GET  /chat/{room_id}

  - ```json
    {
        "results": [
            {"user_name": "유저 정보", "content": "채팅 내용", "created_at": "작성 일시"},
            {"user_name": "유저 정보", "content": "채팅 내용", "created_at": "작성 일시"},
            {"user_name": "유저 정보", "content": "채팅 내용", "created_at": "작성 일시"},
            ....
        ]
    }
    ```

    - 가장 최근 메시지가 노출되어야한다.
    - 채팅참여자는 모든 메시지와 새로운 메시지를 볼 수 있다.

- 채팅방 입장 API
  - POST /chat/{room_id}

  - ```json
    // body
    {
        "user_name": "유저 고유 식별 정보"
    }
    ```
    
- 채팅방 퇴장 API
  - PUT /chat/{room_id}

  - ```json
    // body
    {
        "user_name": "유저 고유 식별 정보"
    }
    ```

- 채팅방 정보 API (optional)
  - GET /chat/{room_id}/info
  
  - ```json
    {
        "user_list": [],
        "user_count_in_30_min": 0
    }
    ```