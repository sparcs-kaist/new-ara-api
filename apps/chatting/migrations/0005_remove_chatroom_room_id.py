# Generated by Django 4.2.23 on 2025-07-04 13:27

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("chatting", "0004_alter_chatroommembership_subscribed"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="chatroom",
            name="room_id",
        ),
    ]
