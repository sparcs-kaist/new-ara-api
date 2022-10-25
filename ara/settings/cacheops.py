from ara.settings import REDIS_HOST


CACHEOPS_REDIS = {
    "host": REDIS_HOST,
    "port": 6379,
    "db": 1,
}

CACHEOPS = {
    "core.Board": {"ops": {"get", "fetch"}, "timeout": 60 * 60},
    "core.Topic": {"ops": {"get", "fetch"}, "timeout": 60 * 60},
    "auth.User": {"ops": {"get"}, "timeout": 60 * 10},
}
