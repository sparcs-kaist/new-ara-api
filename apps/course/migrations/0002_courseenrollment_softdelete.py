import datetime

import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("course", "0001_initial"),
    ]

    operations = [
        # 옛 unique 제약 제거 후 deleted_at 포함 unique 로 교체 (재수강 케이스).
        migrations.RemoveConstraint(
            model_name="courseenrollment",
            name="enrollment_unique_user_course",
        ),
        # MetaDataModel 의 created_at 형식으로 정렬 (auto_now_add → default).
        migrations.AlterField(
            model_name="courseenrollment",
            name="created_at",
            field=models.DateTimeField(
                db_index=True,
                default=django.utils.timezone.now,
                verbose_name="생성 시간",
            ),
        ),
        migrations.AddField(
            model_name="courseenrollment",
            name="updated_at",
            field=models.DateTimeField(
                # auto_now 는 save() 시점 갱신용. 마이그레이션 시점에 기존 row 를
                # 채울 default 를 별도 명시 (Django 가 prompt 안 띄우게).
                # preserve_default=False 로 모델 정의에는 default 가 새지 않게 한다.
                auto_now=True,
                db_index=True,
                default=django.utils.timezone.now,
                verbose_name="수정 시간",
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="courseenrollment",
            name="deleted_at",
            field=models.DateTimeField(
                db_index=True,
                default=datetime.datetime(1, 1, 1, 0, 0, tzinfo=datetime.timezone.utc),
                verbose_name="삭제 시간",
            ),
        ),
        migrations.AddConstraint(
            model_name="courseenrollment",
            constraint=models.UniqueConstraint(
                fields=("user", "course", "deleted_at"),
                name="enrollment_unique_user_course",
            ),
        ),
        migrations.AlterModelOptions(
            name="courseenrollment",
            options={
                "abstract": False,
                "ordering": ("-created_at",),
                "verbose_name": "수강 이력",
                "verbose_name_plural": "수강 이력 목록",
            },
        ),
    ]
