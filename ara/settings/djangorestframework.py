# http://www.django-rest-framework.org/

REST_FRAMEWORK = {
    "DEFAULT_PAGINATION_CLASS": "ara.classes.pagination.PageNumberPagination",
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.OrderingFilter",
    ],
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.AllowAny",),
    "PAGE_SIZE": 15,
    "SERIALIZER_EXTENSIONS": {
        "AUTO_OPTIMIZE": True,
    },
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}
