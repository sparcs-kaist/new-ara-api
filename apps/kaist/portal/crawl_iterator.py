from apps.kaist.portal.crawler import Crawler


class CrawlIterator:
    def __init__(self, start_id: int, limit: int | None = None):
        self.post = Crawler.get_post(start_id)
        self.limit = limit

    def __iter__(self):
        return self

    def __next__(self):
        if self.post is None:
            raise StopIteration

        if self.limit is not None and self.limit <= 0:
            raise StopIteration

        post = self.post
        self.post = Crawler.find_next_post(post)

        if self.limit is not None:
            self.limit -= 1

        return post
