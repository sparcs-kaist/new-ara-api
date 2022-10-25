# Generated by Django 3.2.9 on 2022-05-05 17:37

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0039_add_communication_article"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="communicationarticle",
            name="id",
        ),
        migrations.AlterField(
            model_name="board",
            name="access_mask",
            field=models.IntegerField(default=222, verbose_name="접근 권한 값"),
        ),
        migrations.AlterField(
            model_name="communicationarticle",
            name="article",
            field=models.OneToOneField(
                on_delete=django.db.models.deletion.CASCADE,
                primary_key=True,
                related_name="communication_article",
                serialize=False,
                to="core.article",
                verbose_name="게시물",
            ),
        ),
    ]
