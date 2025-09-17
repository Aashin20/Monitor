import smtplib
import ssl
from email.mime.text import MIMEText
from dotenv import load_dotenv
import os

load_dotenv()

def send_email(student_name: str, recipient_email: str):
  
    sender_email = os.getenv("sender_email")
    sender_password = os.getenv("sender_password")
    
    
    subject = f"Attendance Notification for {student_name}"
    body = f"Dear Parent,\n{student_name} was absent on 16/09/25 for Period 8\n\nBest regards,\nSRMIST"
    message = MIMEText(body)
    message["From"] = sender_email
    message["To"] = recipient_email
    message["Subject"] = subject

    # Send email
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, recipient_email, message.as_string())
        print(f"✅ Email sent to {student_name} ({recipient_email})!")
    
