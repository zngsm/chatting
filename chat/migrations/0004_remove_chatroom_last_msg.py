# Generated by Django 5.1 on 2024-09-05 06:34

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("chat", "0003_alter_chatroom_last_msg"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="chatroom",
            name="last_msg",
        ),
    ]
