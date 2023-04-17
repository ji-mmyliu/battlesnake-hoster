from django.contrib import admin
from django import forms
from .models import Snake
from .utils import server
from battlesnakehoster.widgets import HtmlEditor

from django.contrib import messages

from django.conf import settings
server_cluster = settings.SERVER_CLUSTER


class SnakeAdminForm(forms.ModelForm):
    model = Snake

    class Meta:
        fields = '__all__'
        widgets = {
            'source_code': HtmlEditor(attrs={'style': 'width: 90%; height: 100%;'}),
        }


class SnakeAdmin(admin.ModelAdmin):
    form = SnakeAdminForm
    exclude = ('uuid', 'snake_url',)
    list_display = ('name', 'owner',)

    def get_readonly_fields(self, request, obj=None):
        if obj:  # editing an existing object
            return self.readonly_fields + ('snake_url', 'owner', 'name',)
        else:
            return self.readonly_fields + ('snake_url', 'source_code',)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(owner=request.user)

    def save_model(self, request, snake: Snake, form, change):
        fetched_snake = server.fetch_battlesnake_server(snake)
        if not fetched_snake:
            unique_identifier = snake.uuid.hex[-7:]
            hosted_snake_id = unique_identifier
            hosted_snake_name = f"{snake.name.lower()}-{hosted_snake_id}"
            hosted_snake_url = server_cluster["domain"].format(
                hosted_snake_name)
            snake_url = f"http://{hosted_snake_url}/"
        else:
            snake_url = fetched_snake.url

        messages.info(
            request, f"Successfully deployed your battlesnake! Your snake's URL is {snake_url}")
        super(SnakeAdmin, self).save_model(request, snake, form, change)


admin.site.register(Snake, SnakeAdmin)
