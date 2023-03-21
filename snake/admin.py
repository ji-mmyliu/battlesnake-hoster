from django.contrib import admin
from django import forms
from .models import Snake
from battlesnakehoster.widgets import HtmlEditor

# Register your models here.


class SnakeAdminForm(forms.ModelForm):
    model = Snake

    class Meta:
        fields = '__all__'
        widgets = {
            'source_code': HtmlEditor(attrs={'style': 'width: 90%; height: 100%;'}),
        }


class SnakeAdmin(admin.ModelAdmin):
    form = SnakeAdminForm
    exclude = ('uuid',)

    def get_readonly_fields(self, request, obj=None):
        if obj:  # editing an existing object
            return self.readonly_fields + ('owner',)
        return self.readonly_fields

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(owner=request.user)


admin.site.register(Snake, SnakeAdmin)
