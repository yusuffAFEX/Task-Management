from django.contrib import admin
from django.urls import path

from task_app.views import CreateUserAPIView, LoginAPIView, ListCreateTaskAPIView, RetrieveUpdateDestroyTaskAPIView

urlpatterns = [
    path('register', CreateUserAPIView.as_view()),
    path('login', LoginAPIView.as_view()),
    path('tasks', ListCreateTaskAPIView.as_view()),
    path('tasks/<int:pk>', RetrieveUpdateDestroyTaskAPIView.as_view()),
]