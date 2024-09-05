from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

User = get_user_model()


# Create your tests here.
class TestUser(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_should_create_user(self):
        # Given: 정상적인 유저 생성 폼
        request = {"username": "Suem", "password": "1234"}

        # When: 유저 생성 요청시
        response = self.client.post("/accounts/", data=request)

        # Then: 유저가 생성된다.
        assert response.status_code == status.HTTP_201_CREATED
        assert User.objects.filter(username="Suem").exists()
