import json

from django.conf import settings
from redis import Redis as PyRedis
from redis.client import Pipeline as PyRedisPipeline


class PrefixedRedis(PyRedis):
    def __init__(self, key_prefix, *args, **kwargs):
        self.key_prefix = key_prefix
        super().__init__(*args, **kwargs)

    def get(self, name):
        return super().get(f'{self.key_prefix}{name}')

    def set(self, name, value, **kwargs):
        return super().set(f'{self.key_prefix}{name}', value, **kwargs)

    def setex(self, name, time, value):
        return super().setex(f'{self.key_prefix}{name}', time, value)

    def delete(self, *names):
        return super().delete(*[f'{self.key_prefix}{name}' for name in names])

    def scan_iter(self, match=None, count=None):
        scanned = super().scan_iter(f'{self.key_prefix}{match}' if match is not None else None, count)
        return [x.decode().replace(self.key_prefix, '') for x in scanned]

    def hget(self, name, key):
        return super().hget(f'{self.key_prefix}{name}', key)

    def hgetall(self, name):
        return super().hgetall(f'{self.key_prefix}{name}')

    def hset(self, name, key, value):
        return super().hset(f'{self.key_prefix}{name}', key, value)

    def zadd(self, name, mapping, **kwargs):
        return super().zadd(f'{self.key_prefix}{name}', mapping, **kwargs)

    def zrem(self, name, value, **kwargs):
        return super().zrem(f'{self.key_prefix}{name}', name, value)

    def zrange(self, name, start, end, **kwargs):
        return super().zrange(f'{self.key_prefix}{name}', start, end, **kwargs)

    def zrangebyscore(self, name, min, max, **kwargs):
        return super().zrangebyscore(f'{self.key_prefix}{name}', min, max, **kwargs)

    def get_objs_by_values(self, name, from_value, to_value, preprocess=(lambda x: x)):
        objs = []
        for row in self.zrangebyscore(name, from_value, to_value):
            objs.append(preprocess(row.decode()))

        return objs

    def get_objs_by_indexes(self, name, from_index, to_index, preprocess=(lambda x: x)):
        objs = []
        for row in self.zrange(name, from_index, to_index):
            objs.append(preprocess(row.decode()))

        return objs

    def zremrangebyscore(self, name, min, max):
        return super().zremrangebyscore(f'{self.key_prefix}{name}', min, max)

    def zrevrangebyscore(self, name, min, max, **kwargs):
        return super().zrevrangebyscore(f'{self.key_prefix}{name}', max, min, **kwargs)

    def zpopmin(self, name, count=None):
        return super().zpopmin(f'{self.key_prefix}{name}', count)

    def zcard(self, name):
        return super().zcard(f'{self.key_prefix}{name}')

    def zcount(self, name, min, max):
        return super().zcount(f'{self.key_prefix}{name}', min, max)

    def pipeline(self, transaction=None, shard_hint=None):
        return Pipeline(
            self.key_prefix,
            self.connection_pool,
            self.response_callbacks,
            transaction,
            shard_hint,
        )

    def flushall(self, **kwargs):
        if getattr(settings, 'TEST', False):
            for key in self.scan_iter('*'):
                self.delete(key)


class Redis(PrefixedRedis):
    def __init__(self, host, key_prefix, **kwargs):
        super().__init__(key_prefix, host=host, **kwargs)


class Pipeline(PrefixedRedis, PyRedisPipeline):
    def __init__(self, key_prefix, connection_pool, response_callbacks, transaction, shard_hint):
        super().__init__(key_prefix, connection_pool, response_callbacks, transaction, shard_hint)


redis = Redis(settings.REDIS_HOST, 'newara:', db=settings.REDIS_DATABASE)
