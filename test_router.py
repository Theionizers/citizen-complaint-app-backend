import hostinger_mail_api
from hostinger_mail_api.rest import ApiException



MAILBOX_ID = "AC6ae9143aced4288f18608246b30e"

TO_EMAIL = "pwallah69@gmail.com"

configuration = hostinger_mail_api.Configuration(
    access_token=API_KEY
)

with hostinger_mail_api.ApiClient(configuration) as api_client:

    api = hostinger_mail_api.SendApi(api_client)

    try:
        request = hostinger_mail_api.V1SendRequest(
            from_={
                "address": "info@janamaan.com"
            },
            to=[
                TO_EMAIL
            ],
            subject="OZOCO Test Email",
            text="This is a test email sent using the Hostinger Mail API."
        )

        response = api.send_email(
            mailbox_resource_id=MAILBOX_ID,
            v1_send_request=request
        )

        print("EMAIL SENT SUCCESSFULLY")
        print(response)

    except ApiException as e:
        print("FAILED")
        print("Status:", e.status)
        print("Reason:", e.reason)
        print("Body:", e.body)