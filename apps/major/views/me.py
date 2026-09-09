from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.major.access import user_major_info


class MeView(APIView):
    """현재 로그인 유저의 학과 정보를 반환.

    SSO(kaist_v2_info) 원본 blob 대신 학과 식별자/이름만 추려서 내려준다.
    여기서 주는 std_dept_id 를 그대로 /api/majors/<std_dept_id>/ URL 에
    사용하면 된다.

    응답 예:
        {
            "std_dept_id": 4581,
            "major_name": "새내기과정학부",
            "major_name_eng": "School of Freshman"
        }
    """

    @method_decorator(ensure_csrf_cookie)
    def get(self, request):
        if not request.user.is_authenticated:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        info = user_major_info(request.user)
        if info is None:
            # Profile 또는 SSO major info가 없으면 `404`를 반환한다.
            return Response(
                {"detail": "학과 정보를 확인할 수 없습니다."},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(info, status=status.HTTP_200_OK)
