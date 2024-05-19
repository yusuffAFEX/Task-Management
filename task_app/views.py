from django.shortcuts import render
from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from rest_framework.generics import CreateAPIView, ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView

from task_app.models import Task
from task_app.serializers import CreateUserSerializer, CTokenObtainPairSerializer, CreateListTaskSerializer, \
    UpdateTaskSerializer


# Create your views here.


class CreateUserAPIView(CreateAPIView):
    serializer_class = CreateUserSerializer


class LoginAPIView(TokenObtainPairView):
    serializer_class = CTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            user = serializer.user or request.user
            print(user)

            request.user = user
            response_data = {"id": user.id, "username": user.username,
                             'access_token': serializer.validated_data.get('access')}

            return Response(data=response_data, status=status.HTTP_200_OK)

        return Response(data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ListCreateTaskAPIView(ListCreateAPIView):
    serializer_class = CreateListTaskSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        queryset = Task.active_objects.filter(created_by=self.request.user).order_by('-created_at')
        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        serializer = self.get_serializer(page, many=True)
        return Response({
            "message": "Task List",
            "responseCode": "100",
            'count': self.paginator.page.paginator.count,
            'next': self.paginator.get_next_link(),
            'previous': self.paginator.get_previous_link(),
            "data": serializer.data,
        })


class RetrieveUpdateDestroyTaskAPIView(RetrieveUpdateDestroyAPIView):
    serializer_class = UpdateTaskSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Response(status=status.HTTP_200_OK)
        if self.request.method == 'DELETE':
            return Task.objects.filter(created_by=self.request.user)
        return Task.active_objects.filter(created_by=self.request.user)

    def get_object(self):
        obj = super().get_object()
        if self.request.method == 'GET':
            return obj
        elif self.request.method == 'DELETE':
            if self.request.user != obj.created_by:
                raise PermissionDenied("You do not have permission to perform this action.")
            obj = Task.objects.filter(created_by=self.request.user).first()
            return obj
        else:
            if self.request.user != obj.created_by:
                raise PermissionDenied("You do not have permission to perform this action.")
            return obj

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        print(instance)
        instance.is_deleted = not instance.is_deleted
        instance.save()
        if instance.is_deleted:
            return Response(data="Deleted Successfully!", status=status.HTTP_204_NO_CONTENT)
        return Response(data="Retrieved Successfully!", status=status.HTTP_200_OK)
