# Generated by Django 5.1 on 2024-09-04 15:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("chat", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="chatroomvisit",
            name="last_visited_at",
            field=models.DateTimeField(db_index=True, null=True),
        ),
        migrations.AlterField(
            model_name="message",
            name="created_at",
            field=models.DateTimeField(auto_now=True, db_index=True),
        ),
    ]
