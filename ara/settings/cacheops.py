from .redis import REDIS_HOST, REDIS_PORT

CACHEOPS_REDIS = {
    "host": REDIS_HOST,
    "port": REDIS_PORT,
    "db": 1,
}

CACHEOPS = {
    "core.Board": {"ops": {"get", "fetch"}, "timeout": 60 * 60},
    "core.Topic": {"ops": {"get", "fetch"}, "timeout": 60 * 60},
    "auth.User": {"ops": {"get"}, "timeout": 60 * 10},
}
