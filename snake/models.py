from django.db import models
from django.contrib.auth.models import User
from django.contrib.auth import get_user
import uuid

# Create your models here.


class Snake(models.Model):
    name = models.CharField(verbose_name="Snake Name", max_length=200)
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4)
    owner = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="snake")
    source_code = models.TextField(
        help_text="Your Battlesnake source code in Java. Refer to https://battlesnake.mcpt.jimmyliu.dev/getting_started/java.html for details")

    def __str__(self):
        return f"{self.name} by {self.owner.username}"
