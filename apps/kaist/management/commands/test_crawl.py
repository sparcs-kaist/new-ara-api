from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from tqdm import tqdm

from apps.core.models import Article
from apps.kaist.models import Post
from apps.kaist.portal.crawl_iterator import CrawlIterator
from apps.user.models import UserProfile
from ara.log import log

PORTAL_NOTICE_BOARD_ID = 1

User = get_user_model()


class Command(BaseCommand):
    help = "Crawl and save posts from the latest saved post up to the specified batch size."

    def add_arguments(self, parser):
        parser.add_argument(
            "--batch-size",
            default=32,
            type=int,
            help="Number of posts to crawl",
        )
        parser.add_argument(
            "--visualize",
            action="store_true",
            help="Visualize crawling progress",
        )

    def handle(self, *args, **options):
        posts = self.fetch_from_the_latest(
            batch_size=options["batch_size"],
            visualize=options["visualize"],
        )

        with transaction.atomic():
            Post.objects.bulk_create(
                objs=posts,
                update_conflicts=True,
                update_fields=(
                    "title",
                    "content",
                    "next_post_id",
                    "view_count",
                    "changed_at",
                    "changed_user_id",
                    "updated_at",
                ),
            )

            # Create users and articles for newly fetched posts
            for post in posts[1:]:
                user, is_user_created = User.objects.update_or_create(
                    username=post.writer_id,
                    defaults={
                        "first_name": post.writer_name,
                        "email": post.writer_email or "",
                        "is_active": False,
                    },
                )
                if is_user_created:
                    UserProfile.objects.create(
                        user=user,
                        nickname=post.writer_name,
                        picture="user_profiles/default_pictures/KAIST-logo.png",
                        is_newara=False,
                    )

                # TODO: Save portal image if needed
                # TODO: Enable disabled hyperlinks (wrap it with <a> tag)

                Article.objects.create(
                    parent_board_id=PORTAL_NOTICE_BOARD_ID,
                    title=post.title,
                    content=post.content,
                    created_by=user,
                    url=f"https://portal.kaist.ac.kr/kaist/portal/board/ntc/0#{post.id}",
                    created_at=post.registered_at,
                )

        # TODO: Send slack message with the number of posts fetched

        log.info("All Done!")

    @staticmethod
    def fetch_from_the_latest(batch_size: int, visualize: bool):
        """
        Crawl posts from the latest saved post up to the specified batch size.

        :param batch_size: The number of posts to crawl at once
        :param visualize: Whether to visualize the crawling progress
        """

        latest_post = Post.objects.latest("registered_at")

        iterator = CrawlIterator(start_id=latest_post.id, limit=batch_size)
        if visualize:
            iterator = tqdm(iterator, total=batch_size)

        return list(iterator)
