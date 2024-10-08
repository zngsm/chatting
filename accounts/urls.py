from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView

from accounts import views

urlpatterns = [
    path("", views.create_user),
    path("login/", TokenObtainPairView.as_view()),
]
