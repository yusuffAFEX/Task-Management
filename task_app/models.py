from django.contrib.auth.models import User
from django.db import models

# Create your models here.
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.urls import reverse
from PIL import Image


class ActiveTask(models.Manager):
    def get_queryset(self):
        return super(ActiveTask, self).get_queryset().filter(is_deleted=False)


class Task(models.Model):
    title = models.CharField(max_length=200)
    assigned_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='assigned_users')
    description = models.TextField(blank=True)
    is_completed = models.BooleanField(default=False)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    start_date = models.DateField()
    due_date = models.DateField()
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = models.Manager()
    active_objects = ActiveTask()

    def __str__(self):
        return self.title


class Profile(models.Model):
    image = models.ImageField(null=True, blank=True, upload_to='media/photos')
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.user.first_name} Profile'

    def save(self, *args, **kwargs):
        super(Profile, self).save()
        if self.image:
            image = Image.open(self.image.path)
            if image.height > 300 and image.width > 300:
                size = (200, 200)
                image.thumbnail(size)
                image.save(self.image.path)


@receiver(post_save, sender=User)
def create_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)