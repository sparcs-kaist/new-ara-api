from typing import Any

from django.core.management.base import BaseCommand, CommandError, CommandParser

from apps.core.models import Article


class Command(BaseCommand):
    help = "Restore missing search text for JSON articles. Rebuild the search index afterwards."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("--batch-size", type=int, default=500)

    def handle(self, *args: Any, **options: Any) -> None:
        batch_size = options["batch_size"]
        if batch_size < 1:
            raise CommandError("--batch-size must be positive")
        last_id = 0
        updated = 0
        while True:
            articles = list(
                Article.objects.filter(
                    id__gt=last_id, content_text="", content__startswith="{"
                )
                .only("id", "content", "content_text")
                .order_by("id")[:batch_size]
            )
            if not articles:
                break
            last_id = articles[-1].id
            changed = []
            for article in articles:
                article.content_text = article.extract_text_from_json(article.content)
                if article.content_text:
                    changed.append(article)
            Article.objects.bulk_update(
                changed, ["content_text"], batch_size=batch_size
            )
            updated += len(changed)
        self.stdout.write(f"Restored content_text for {updated} articles.")
        self.stdout.write("Run: python manage.py search_index --rebuild")
