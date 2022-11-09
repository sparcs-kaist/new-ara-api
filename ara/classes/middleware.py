from django.urls import resolve


class CheckTermsOfServiceMiddleware:
    ALLOWED_URL_NAMES = [
        "me",
        "user-sso-login",
        "user-sso-login-callback",
        "userprofile-agree-terms-of-service",
        "InvalidSsoLoginView",
    ]

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        if resolve(request.path_info).url_name not in self.ALLOWED_URL_NAMES and (
            request.user.is_authenticated
            and request.user.profile.agree_terms_of_service_at is None
        ):
            response.content = ""
            response.status_code = (
                418  # Use unusual http status code for avoiding conflict
            )

            return response

        return response
