import os

from slack_sdk.webhook import WebhookClient

SLACK_WEBHOOK_URL = os.environ.get("SLACK_WEBHOOK_URL")

slack_webhook_client = WebhookClient(url=SLACK_WEBHOOK_URL)
