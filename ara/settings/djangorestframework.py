# http://www.django-rest-framework.org/

REST_FRAMEWORK = {
    'DEFAULT_PAGINATION_CLASS': 'ara.classes.pagination.PageNumberPagination',
    'DEFAULT_FILTER_BACKENDS': (
        'rest_framework_filters.backends.RestFrameworkFilterBackend',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.AllowAny',
    ),
}
