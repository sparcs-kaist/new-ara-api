OVERRIDE_KEY = 'ignore_cache'


def cache_by_user(func):
    def wrapper(*args, **kwargs):
        instance = args[0]
        user = args[1]
        ignore_cache = OVERRIDE_KEY in kwargs and kwargs[OVERRIDE_KEY] is True

        cache_key = f'USER_CACHE-{func.__name__}-{user.id}'
        if cache_key not in instance.__dict__ or ignore_cache:
            instance.__dict__[cache_key] = func(*args, **kwargs)
        return instance.__dict__[cache_key]

    return wrapper

