import os
from dotenv import load_dotenv
from automation.email_sender import EmailSender

# Load env variables manually to check if they are being read
load_dotenv()

print("--- Email Debug Tool ---")
print(f"EMAIL_USER: {os.getenv('EMAIL_USER')}")
# Mask password for security in logs
pwd = os.getenv('EMAIL_PASS')
print(f"EMAIL_PASS: {'*' * len(pwd) if pwd else 'None'}")
print(f"SMTP_SERVER: {os.getenv('SMTP_SERVER')}")

sender = EmailSender()

recipient = input("Enter a recipient email address to test: ")

print(f"Attempting to send test email to {recipient}...")
success, msg = sender.send_email(recipient, "Test Email from AI Assistant", "This is a test email to verify the backend configuration.")

if success:
    print("SUCCESS: Email sent successfully!")
else:
    print(f"FAILURE: {msg}")
    print("\nTroubleshooting Tips:")
    print("1. Ensure EMAIL_USER is your full Gmail address.")
    print("2. Ensure EMAIL_PASS is an 'App Password', NOT your login password.")
    print("   (Go to Google Account -> Security -> 2-Step Verification -> App Passwords)")
    print("3. Check internet connection.")
input("\nPress Enter to exit...")
