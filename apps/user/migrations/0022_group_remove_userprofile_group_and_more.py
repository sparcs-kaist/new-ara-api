# Generated by Django 4.2.3 on 2024-01-10 17:16

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


def add_groups(apps, schema_editor):
    default_groups = {
        1: ("Unauthorized user", "뉴아라 계정을 만들지 않은 사람들", False),
        2: ("KAIST member", "카이스트 메일을 가진 사람 (학생, 교직원)", False),
        3: ("Store employee", "교내 입주 업체 직원", False),
        4: ("Other member", "카이스트 메일이 없는 개인 (특수한 관련자 등)", False),
        5: ("KAIST organization", "교내 학생 단체들", True),
        6: ("External organization", "외부인 (홍보 계정 등)", True),
        7: ("Communication board admin", "소통게시판 관리인", False),
        8: ("News board admin", "뉴스게시판 관리인", False),
    }

    Group = apps.get_model("user", "Group")
    for group_id, (name, description, is_official) in default_groups.items():
        Group.objects.create(
            group_id=group_id,
            name=name,
            description=description,
            is_official=is_official,
        )


def add_user_groups(apps, schema_editor):
    cursor = schema_editor.connection.cursor()
    cursor.execute(
        """
        INSERT INTO user_usergroup (user_id, group_id)
        SELECT a.user_id, (a.group+1) FROM user_userprofile a, user_group b
        WHERE (a.group+1) = b.group_id;
    """
    )
    cursor.close()


def fix_manualuser_org_type(apps, schema_editor):
    cursor = schema_editor.connection.cursor()
    cursor.execute(
        """
        UPDATE user_manualuser
        SET org_type = org_type + 1;
    """
    )
    cursor.close()


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("user", "0021_remove_userprofile_extra_preferences"),
    ]

    operations = [
        migrations.CreateModel(
            name="Group",
            fields=[
                (
                    "group_id",
                    models.AutoField(
                        db_index=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="Group ID",
                    ),
                ),
                ("name", models.CharField(max_length=32, verbose_name="Group name")),
                (
                    "description",
                    models.CharField(
                        max_length=128, null=True, verbose_name="Group description"
                    ),
                ),
                (
                    "is_official",
                    models.BooleanField(default=False, verbose_name="공식 단체 또는 학생단체"),
                ),
            ],
            options={
                "verbose_name": "Group",
                "verbose_name_plural": "Groups",
            },
        ),
        migrations.CreateModel(
            name="UserGroup",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "group",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="user.group",
                        verbose_name="그룹",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="사용자",
                    ),
                ),
            ],
            options={
                "verbose_name": "사용자 그룹",
                "verbose_name_plural": "사용자가 속한 그룹 목록",
                "unique_together": {("user", "group")},
            },
        ),
        migrations.RunPython(add_groups),
        migrations.RunPython(add_user_groups),
        migrations.RunPython(fix_manualuser_org_type),
        migrations.RemoveField(
            model_name="userprofile",
            name="group",
        ),
        migrations.AlterField(
            model_name="manualuser",
            name="org_type",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="user.group",
                verbose_name="업체/단체 그룹",
            ),
        ),
    ]
