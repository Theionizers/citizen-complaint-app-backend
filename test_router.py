# app/services/test_email.py

from app.services.email_service import send_email


send_email(
    to_email="pwallah69@gmail.com",
    subject="OZOCO SMTP Test",
    html="""
    <h2>SMTP test successful</h2>
    <p>This email was sent from the OZOCO backend.</p>
    """,
)

print("Email sent successfully")