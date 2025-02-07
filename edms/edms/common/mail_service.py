import logging

from django.conf import settings
import json
import requests
logger = logging.getLogger(__name__)


def send_email(to_email: str, subject: str, text_content: str):
    url = "https://api.brevo.com/v3/smtp/email"
    payload = json.dumps(
        {
            "sender": {"name": "DMT E-Office", "email": settings.SEND_FROM_EMAIL},
            "to": [{"email": f"{to_email}"}],
            "subject": subject,
            "textContent": text_content,
        }
    )
    headers = {
        "accept": "application/json",
        "api-key": settings.BREVO_API_KEY,
        "content-type": "application/json",
    }
    response = requests.request("POST", url, headers=headers, data=payload)
    logger.info(response.text)
    return response


def send_mail_forgot_password(email_to, token):
    logger.info(f"token: {token}")
    send_email(
        to_email=email_to,
        subject="[DMT E-Office] Đặt lại mật khẩu của bạn",
        text_content=f"""
        Vui lòng sử dụng liên kết bên dưới để đặt lại mật khẩu. Liên kết này chỉ có hiệu lực trong 1 giờ tới.

        Hi {email_to},

        Bạn vừa yêu cầu đặt lại mật khẩu cho tài khoản [DMT E-Office] của mình.

        Đặt lại mật khẩu ( {settings.FE_DOMAIN}?token={token} )

        Nếu bạn không yêu cầu đặt lại mật khẩu, hãy bỏ qua email này hoặc liên hệ với bộ phận hỗ trợ (thuanphuocsoftware@gmail.com) nếu cần thêm thông tin.

        Trân trọng
        Đội ngũ [DMT E-Office]
        """
    )
