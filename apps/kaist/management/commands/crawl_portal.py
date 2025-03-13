from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from tqdm import tqdm

from apps.core.models import Article
from apps.kaist.models import Post
from apps.kaist.portal.crawl_iterator import CrawlIterator
from apps.kaist.portal.crawler import SessionExpiredException
from apps.user.models import UserProfile
from ara.log import log
from library.slack.webhook import slack_webhook_client

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
        try:
            posts = self.fetch_from_the_latest(
                batch_size=options["batch_size"],
                visualize=options["visualize"],
            )
        except SessionExpiredException:
            self._send_session_expired_alert()
            return

        new_posts = posts[1:]
        if not new_posts:
            self._send_no_new_post_alert()
            return

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

            for post in new_posts:
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

        self._send_success_alert(post_count=len(posts))

    def fetch_from_the_latest(self, batch_size: int, visualize: bool):
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

    def _send_success_alert(self, post_count: int):
        slack_webhook_client.send(
            text=f":blobhaj_ghostie_alive: 공지 {post_count}개를 가져왔어요! 크앙!"
        )
        log.info(f"KAIST Portal Crawler :: Fetched {post_count} new posts")

    def _send_no_new_post_alert(self):
        slack_webhook_client.send(text=f":blobhaj_ghostie_alive: 새로운 공지가 없어요.")
        log.info("KAIST Portal Crawler :: No new post found")

    def _send_session_expired_alert(self):
        slack_webhook_client.send(
            blocks=[
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": ":blobhaj_ghostie_surprise: 세션이 만료되었어요! <!here>",
                    },
                }
            ]
        )
        log.error("KAIST Portal Crawler :: JSESSIONID has expired")
