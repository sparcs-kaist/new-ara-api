# Generated by Django 4.2.23 on 2025-07-20 02:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("chatting", "0007_alter_chatmessage_options_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="chatroom",
            name="picture",
            field=models.ImageField(
                blank=True,
                default=None,
                null=True,
                upload_to="chat_room/pictures",
                verbose_name="채팅방 이미지",
            ),
        ),
    ]
