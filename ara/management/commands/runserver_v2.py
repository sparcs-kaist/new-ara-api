import uvicorn
from django.core.management import BaseCommand
from django.core.management.base import CommandParser


class Command(BaseCommand):
    def add_arguments(self, parser: CommandParser) -> None:
        super().add_arguments(parser)
        # positional argument
        parser.add_argument("server", type=str, help="address")

    def handle(self, *args, **options):
        server: str = options["server"]
        host = server.split(":")[0]
        port: int = int(server.split(":")[1])
        uvicorn.run("ara.wsgi:app", host=host, port=port, reload=True)
