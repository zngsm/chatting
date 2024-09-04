from django.urls import path

from accounts import views

urlpatterns = [
    path("", views.create_user),
]
