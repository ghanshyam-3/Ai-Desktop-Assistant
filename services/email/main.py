from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
import uvicorn
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = FastAPI(title="Email Service")

class EmailRequest(BaseModel):
    recipient: str
    subject: str
    body: str

@app.get("/")
def home():
    return {"status": "Email Service Running", "port": 8003}

@app.post("/send-email")
def send_email(email_req: EmailRequest):
    """
    Sends an email using SMTP.
    """
    sender_email = os.getenv("EMAIL_USER")
    sender_password = os.getenv("EMAIL_PASSWORD")
    smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))

    if not sender_email or not sender_password:
        return {"status": "error", "message": "Email credentials not configured."}

    try:
        # Create message
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = email_req.recipient
        msg['Subject'] = email_req.subject
        msg.attach(MIMEText(email_req.body, 'plain'))

        # Connect to server
        print(f"Connecting to SMTP server {smtp_server}:{smtp_port}...")
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        
        # Login
        print(f"Logging in as {sender_email}...")
        server.login(sender_email, sender_password)
        
        # Send
        print(f"Sending email to {email_req.recipient}...")
        server.send_message(msg)
        server.quit()
        
        return {"status": "success", "message": f"Email sent to {email_req.recipient}"}

    except Exception as e:
        print(f"Email Error: {e}")
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    # Load .env explicitly if running standalone
    load_dotenv()
    uvicorn.run(app, host="0.0.0.0", port=8003)
