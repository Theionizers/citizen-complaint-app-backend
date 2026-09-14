import smtplib
import ssl

from email.message import EmailMessage

from app.core.config import settings


def send_email(
    to_email: str,
    subject: str,
    html: str,
):
    message = EmailMessage()

    message["From"] = settings.EMAIL_FROM
    message["To"] = to_email
    message["Subject"] = subject

    message.set_content(
        "Please open this email in an HTML-compatible email client."
    )

    message.add_alternative(
        html,
        subtype="html"
    )

    context = ssl.create_default_context()

    with smtplib.SMTP_SSL(
        settings.SMTP_HOST,
        settings.SMTP_PORT,
        context=context,
        timeout=30,
    ) as server:

        server.login(
            settings.SMTP_USERNAME,
            settings.SMTP_PASSWORD,
        )

        server.send_message(message)