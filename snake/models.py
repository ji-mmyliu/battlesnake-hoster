from django.db import models
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.auth import get_user

from django.db.models.signals import post_delete
from django.dispatch import receiver

import uuid
import os

from .utils import server


class Snake(models.Model):
    name = models.CharField(verbose_name="Snake Name",
                            max_length=200)  # TODO: slugify name
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4)
    owner = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="snake")
    source_code = models.TextField(
        help_text="Your Battlesnake source code in Java. Refer to https://battlesnake.mcpt.jimmyliu.dev/getting_started/java.html for details", blank=True)
    snake_url = models.URLField(
        verbose_name="Hosted Battlesnake URL")  # TODO: make into model

    def save(self, *args, **kwargs):
        os.makedirs(f"sources/{self.uuid}", exist_ok=True)
        with open(f"sources/{self.uuid}/Main.java", "w") as f:
            f.write(self.source_code)
            f.flush()

        snake_server = server.fetch_battlesnake_server(self)
        if not snake_server:
            snake_server = server.create_battlesnake_server(self)

        self.snake_url = snake_server.url

        server.update_source_code(self, f"sources/{self.uuid}/Main.java")

        super(Snake, self).save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} by {self.owner.username}"


@receiver(post_delete, sender=Snake)
def signal_function_name(sender, instance, using, **kwargs):
    server.delete_battlesnake_server(instance)

# class HostedSnake:
#     def __init__(self, id, name, url):
#         self.id = id
#         self.name = name
#         self.url = url
