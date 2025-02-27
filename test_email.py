import smtplib
from email.message import EmailMessage

# Email Configuration
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SENDER_EMAIL = "gomezchristian925@gmail.com"  # Your Gmail
SENDER_PASSWORD = "gwadmsxxfgusurru"  # Your App Password
RECIPIENT_EMAIL = "cgomez5@nd.edu"  # Your recipient

# Create email message
msg = EmailMessage()
msg["Subject"] = "Test Email from Python"
msg["From"] = SENDER_EMAIL
msg["To"] = RECIPIENT_EMAIL
msg.set_content("This is a test email to check SMTP connection.")

try:
    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()  # Secure the connection
        server.login(SENDER_EMAIL, SENDER_PASSWORD)  # Login
        server.send_message(msg)  # Send email
    print("✅ Email sent successfully!")
except Exception as e:
    print("❌ Failed to send email:", e)