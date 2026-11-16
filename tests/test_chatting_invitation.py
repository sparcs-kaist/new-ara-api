from rest_framework.test import APIClient


def test_invitation_does_not_allow_update_methods():
    client = APIClient()

    for method in (client.put, client.patch):
        response = method(
            "/api/chat/invitation/1/",
            {"invitation_to": 1},
            format="json",
        )

        assert response.status_code == 405
