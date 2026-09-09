from app.services.email_service import send_email


send_email(
    to_email="sskhilonaghar@gmail.com",
    subject="OZOCO Test Email",
    html="""
    <h1>OZOCO</h1>
    <p>Email service is working correctly.</p>
    """
)

print("Email sent successfully")