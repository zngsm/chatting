from django.contrib.auth import authenticate, get_user_model, login
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from accounts.serializers import UserSerializer

User = get_user_model()


# Create your views here.
@api_view(["POST"])
def create_user(request):
    user = User.objects.create(username=request.data["username"])
    user.set_password(request.data["password"])
    user.save()
    return Response(status=status.HTTP_201_CREATED)
