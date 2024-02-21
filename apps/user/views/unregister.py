import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView


def create_msg(
    title: str, sender_mail: str, message: str, receiver_mail: str
) -> MIMEMultipart:
    msg = MIMEMultipart()
    msg["Subject"] = title
    msg["From"] = sender_mail
    msg.attach(MIMEText(message, "plain"))  # TODO: Use HTML instead of plain text
    msg["To"] = receiver_mail
    return msg


def smtp_send(
    title: str,
    message: str,
    sender_mail: str,
    mailing_list: list[str],
    each: bool = True,
):
    """
    Send email using SMTP relay gmail server.

    each True: Send email to each receiver. Receivers cannot see other receivers.
    each False: Send email to all receivers. Receivers can see other receivers.
    """
    allowed_mail_domains = ("@sparcs.org",)

    if not sender_mail.endswith(allowed_mail_domains):
        raise ValueError("Invalid email domain")

    smtp = smtplib.SMTP("smtp-relay.gmail.com", 587)
    smtp.starttls()
    # smtp.login("", "") # TODO: Use ID, PW instead of IP Address Authentication
    smtp.ehlo()

    if each:
        for receiver in mailing_list:
            # print(f"[{mailing_list.index(receiver) + 1}/{len(mailing_list)}] Sending email to [{receiver}]")  # FOR DEBUG
            msg = create_msg(title, sender_mail, message, receiver)
            smtp.sendmail(sender_mail, receiver, msg.as_string())
    else:
        receivers = ", ".join(mailing_list)
        msg = create_msg(title, sender_mail, message, receivers)
        smtp.sendmail(sender_mail, mailing_list, msg.as_string())

    smtp.quit()


class Unregister(APIView):
    """
    Request to unregister
    """

    @method_decorator(ensure_csrf_cookie)
    def get(self, request):
        if not request.user.is_authenticated:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        message = f"<NewAra 회원 탈퇴 요청>\n\nuserid: {request.user.id}\nuseremail: {request.user.email}\n\n"
        try:
            smtp_send(
                "NewAra 회원 탈퇴 요청",
                message,
                "new-ara@sparcs.org",
                ["new-ara@sparcs.org"],
                False,
            )
            rtn = {"message": "탈퇴 요청이 접수되었습니다. 확인 후 처리하겠습니다."}
            return Response(rtn)
        except Exception as e:
            print("ERROR:", e)
            rtn = {"message": "탈퇴 요청 중 오류가 발생했습니다. 관리자에게 문의해주세요."}
            return Response(rtn, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
