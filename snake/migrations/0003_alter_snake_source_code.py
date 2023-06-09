# Generated by Django 4.1.7 on 2023-03-24 03:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('snake', '0002_snake_snake_url_alter_snake_source_code'),
    ]

    operations = [
        migrations.AlterField(
            model_name='snake',
            name='source_code',
            field=models.TextField(blank=True, help_text='Your Battlesnake source code in Java. Refer to https://battlesnake.mcpt.jimmyliu.dev/getting_started/java.html for details'),
        ),
    ]
