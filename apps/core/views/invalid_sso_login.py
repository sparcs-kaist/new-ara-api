from django.views.generic import TemplateView


class InvalidSsoLoginView(TemplateView):
    template_name = "invalid_sso_login.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # TODO: code 와 status_code 에 따라 다른 해결 방법을 제시할 수 있으면 좋겠습니다.
        # INVALID_METHOD, INVALID_CODE, TOKEN_SERVICE_MISMATCH,
        # TOKEN_EXPIRED, INVALID_SERVICE, INALID_TIMESTAMP, INVALID_SIGN
        # 등의 code 가 있을 수 있습니다.
        # https://github.com/sparcs-kaist/sparcssso/blob/master/apps/api/views/v2.py
        context.update(
            {
                "code": self.request.GET.get("code", ""),
                "status_code": self.request.GET.get("status_code", ""),
            }
        )

        return context
