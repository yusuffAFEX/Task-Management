from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.contrib.auth.models import User, update_last_login
from django.utils import timezone
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainSerializer
from rest_framework_simplejwt.tokens import RefreshToken

from task_app.models import Task
from task_app.utils import EmailAuthenticate

email_authenticate = EmailAuthenticate()


class CreateUserSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(required=False)
    password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)
    email = serializers.EmailField(required=True)
    first_name = serializers.CharField(required=True)
    last_name = serializers.CharField(required=True)
    username = serializers.CharField(required=True)

    class Meta:
        model = User
        fields = ('id', 'first_name', 'last_name', 'username', 'email', 'image', 'password', 'confirm_password', 'date_joined')
        extra_kwargs = {
            "date_joined": {"read_only": True},
            "id": {"read_only": True},
        }

    def validate(self, attrs):
        password = attrs.get('password')
        confirm_password = attrs.get('confirm_password')
        username = attrs.get('username')
        email = attrs.get('email')

        if password != confirm_password:
            raise serializers.ValidationError('Password does not matched!')

        if User.objects.filter(username=username).exists():
            raise serializers.ValidationError('User with username already exist!')

        if User.objects.filter(email=email).exists():
            raise serializers.ValidationError('User with email already exist!')

        return attrs

    def create(self, validated_data):
        # Remove confirm_password from the validated data before creating the User instance
        validated_data.pop('confirm_password', None)
        password = validated_data.pop('password', None)
        image = validated_data.pop('image', None)
        user = User.objects.create_user(**validated_data)
        user.set_password(password)  # set password for the user and hash it
        user.save()
        user.profile.image = image  # user object to profile is OnetoOne relationShip
        user.profile.save(update_fields=['image'])  # save the image field
        return user


class CTokenObtainPairSerializer(TokenObtainSerializer):
    username = serializers.CharField()
    password = serializers.CharField()
    token_class = RefreshToken

    def validate(self, attrs):

        authenticate_kwargs = {'username': attrs['username'], "password": attrs["password"], }
        try:
            authenticate_kwargs["request"] = self.context["request"]
        except KeyError:
            pass

        try:
            print(authenticate_kwargs)
            self.user = email_authenticate.authenticate(**authenticate_kwargs)
        except User.MultipleObjectsReturned:
            raise serializers.ValidationError("Access denied due to mistaken identity", "no_user_found")
        except Exception as e:
            raise serializers.ValidationError(f"Login error: {str(e)}", "no_user_found")

        if self.user is None:
            print(self.user)
            raise serializers.ValidationError("Access denied due to invalid credentials", "no_user_found")

        if not self.user.is_active:
            raise serializers.ValidationError("User is not active", "in_active")

        data = {}

        refresh = self.get_token(self.user)

        data["refresh"] = str(refresh)
        data["access"] = str(refresh.access_token)

        update_last_login(None, self.user)

        return data


class CreateListTaskSerializer(serializers.ModelSerializer):
    created_by = serializers.SerializerMethodField(required=False)
    description = serializers.CharField()
    start_date = serializers.DateField(required=False)

    class Meta:
        model = Task
        fields = ("id", "title", "description", "assigned_user", "is_completed", "created_by", "start_date", "due_date", "created_at", "updated_at")
        extra_kwargs = {
            "created_at": {"read_only": True},
            "updated_at": {"read_only": True},
            "created_by": {"read_only": True},
            "id": {"read_only": True},
        }

    def validate(self, attrs):
        start_date = attrs.get('start_date')
        due_date = attrs.get('due_date')

        if (start_date and start_date < timezone.now().date()) or due_date <= timezone.now().date():
            raise serializers.ValidationError('start date and end date must be future date.')

        if start_date and due_date < start_date:
            raise serializers.ValidationError("due date can't be lesser than start date")

        return attrs

    def get_created_by(self, obj):
        return {"first_name": obj.created_by.first_name, "last_name": obj.created_by.last_name, "email": obj.created_by.email,
                "username": obj.created_by.username}

    def create(self, validated_data):
        author = self.context["request"].user
        start_date = validated_data.get('start_date', None)
        if not start_date:
            validated_data['start_date'] = timezone.now().date()
        validated_data['created_by'] = author
        task = super(CreateListTaskSerializer, self).create(validated_data)

        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            "tasks",  # Channel group name
            {
                "type": "task_message",
                "message": str({
                    "id": task.id,
                    "title": task.title,
                    "description": task.description,
                    "assigned_user": f'{task.assigned_user.first_name} {task.assigned_user.last_name}',
                    "due_date": task.due_date,
                    "is_completed": task.is_completed,
                    "start_date": str(task.start_date),
                    "created_by": task.created_by.username,
                    "created_at": task.created_at,
                    "updated_at": task.updated_at,
                })
            }
        )

        return task


class UpdateTaskSerializer(serializers.ModelSerializer):
    created_by = serializers.SerializerMethodField(required=False)
    description = serializers.CharField()
    start_date = serializers.DateField(required=False)

    class Meta:
        model = Task
        fields = ("id", "title", "description", "assigned_user", "is_completed", "created_by", "start_date", "due_date", "created_at", "updated_at")
        extra_kwargs = {
            "created_at": {"read_only": True},
            "updated_at": {"read_only": True},
            "created_by": {"read_only": True},
            "id": {"read_only": True},
            }

    def get_created_by(self, obj):
        return {"first_name": obj.created_by.first_name, "last_name": obj.created_by.last_name,
                "email": obj.created_by.email,
                "username": obj.created_by.username}

    def validate(self, attrs):
        start_date = attrs.get('start_date')
        due_date = attrs.get('due_date')

        if (start_date and start_date < timezone.now().date()) or (due_date and due_date <= timezone.now().date()):
            raise serializers.ValidationError('start date and end date must be future date.')

        if (start_date and due_date) and (due_date < start_date):
            raise serializers.ValidationError("due date can't be lesser than start date")

        return attrs

    def update(self, instance, validated_data):
        start_date = validated_data.get("start_date")
        due_date = validated_data.get("due_date")
        if (start_date and not due_date) and instance.due_date <= start_date:
            raise serializers.ValidationError("due date can't be lesser than start date")

        if (due_date and not start_date) and instance.start_date >= due_date:
            raise serializers.ValidationError("due date can't be lesser than start date")

        task = super(UpdateTaskSerializer, self).update(instance, validated_data)
        serialized_data = CreateListTaskSerializer(task).data
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            "tasks",  # Channel group name
            {
                "type": "task_message",
                "message": serialized_data
            }
        )

        return task
