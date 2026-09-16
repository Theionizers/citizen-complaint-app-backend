import logging

from hostinger_mail_api.api.send_api import SendApi
from hostinger_mail_api.api_client import ApiClient
from hostinger_mail_api.configuration import Configuration
from hostinger_mail_api.models.v1_send_request import V1SendRequest

from app.core.config import settings

logger = logging.getLogger(__name__)


def send_email(
    to_email: str,
    subject: str,
    html: str,
):
    request = V1SendRequest(
        to=[to_email],
        subject=subject,
        text="Please open this email in an HTML-compatible email client.",
        html=html,
    )

    configuration = Configuration(
        access_token=settings.HOSTINGER_API_KEY,
    )

    try:
        with ApiClient(configuration) as api_client:
            api = SendApi(api_client)
            api.send_email(
                mailbox_resource_id=settings.HOSTINGER_MAILBOX_RESOURCE_ID,
                v1_send_request=request,
            )
    except Exception as error:
        logger.error(
            "Hostinger email delivery failed: %s",
            type(error).__name__,
        )
        raise RuntimeError("Unable to send email") from error