# http://www.django-rest-framework.org/

REST_FRAMEWORK = {
    "DEFAULT_PAGINATION_CLASS": "ara.classes.pagination.PageNumberPagination",
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "django_filters.rest_framework.OrderingFilter",
    ],
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.AllowAny",),
    "PAGE_SIZE": 15,
    "SERIALIZER_EXTENSIONS": {
        "AUTO_OPTIMIZE": True,
    },
}
