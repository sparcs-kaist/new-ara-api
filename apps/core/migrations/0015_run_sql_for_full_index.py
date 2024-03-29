# Generated by Jooyon

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0014_auto_20200825_1955"),
    ]

    operations = [
        migrations.RunSQL(
            sql="CREATE FULLTEXT INDEX `idx_title` on core_article(`title`);",
            reverse_sql="ALTER TABLE core_article DROP INDEX idx_title",
        ),
        migrations.RunSQL(
            sql="CREATE FULLTEXT INDEX `idx_content_text` on core_article(`content_text`);",
            reverse_sql="ALTER TABLE core_article DROP INDEX idx_content_text",
        ),
    ]
