import os
import os.path
import base64
import json
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from sqlalchemy.orm import Session
from database.db import SessionLocal
from database.models import EmailContact, EmailLog

# If modifying these scopes, delete the file token.json.
SCOPES = [
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.labels'
]

class GmailService:
    def __init__(self):
        self.creds = None
        self.service = None
        self._try_load_token()   # silent load only — never prompts at startup

    def _try_load_token(self):
        """Silently load & refresh token. Never opens a browser. Called at startup."""
        creds_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'credentials.json')
        token_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'token.json')

        if os.path.exists(token_path):
            try:
                self.creds = Credentials.from_authorized_user_file(token_path, SCOPES)
            except Exception:
                self.creds = None

        if self.creds and self.creds.expired and self.creds.refresh_token:
            try:
                self.creds.refresh(Request())
                # Save refreshed token
                with open(token_path, 'w') as token:
                    token.write(self.creds.to_json())
            except Exception as e:
                print(f"[Gmail] Token refresh failed ({e}). Run 'python scripts/auth_gmail.py' to re-authorize.")
                self.creds = None

        if self.creds and self.creds.valid:
            try:
                self.service = build('gmail', 'v1', credentials=self.creds)
                print("Gmail Service Authenticated Successfully.")
            except Exception as e:
                print(f"[Gmail] Service build failed: {e}")
        else:
            if not (self.creds and self.creds.valid):
                print("[Gmail] No valid token — Gmail features disabled. Run 'python scripts/auth_gmail.py' to re-authorize.")

    def authenticate(self):
        """Full re-authentication with browser flow. Call this only from auth_gmail.py script."""
        creds_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'credentials.json')
        token_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'token.json')

        self._try_load_token()

        # If still not valid, launch browser flow
        if not self.creds or not self.creds.valid:
            if os.path.exists(creds_path):
                try:
                    flow = InstalledAppFlow.from_client_secrets_file(creds_path, SCOPES)
                    # "prompt='consent'" forces Google to return a refresh token
                    self.creds = flow.run_local_server(port=0, prompt='consent')
                    with open(token_path, 'w') as token:
                        token.write(self.creds.to_json())
                    self.service = build('gmail', 'v1', credentials=self.creds)
                    print("Gmail re-authorized successfully.")
                except Exception as e:
                    print(f"[Gmail] Authentication failed: {e}")
            else:
                print(f"[Gmail] credentials.json not found at {creds_path}")

    def send_email(self, to_email, subject, body):
        """Sends an email and logs it"""
        if not self.service:
            # Try re-auth once
            self.authenticate()
            if not self.service:
                return False, "Gmail Service not authenticated. Please run auth script."

        try:
            message = MIMEMultipart()
            message['to'] = to_email
            message['subject'] = subject
            msg = MIMEText(body)
            message.attach(msg)

            raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
            create_message = {'raw': raw}

            sent_message = self.service.users().messages().send(userId="me", body=create_message).execute()
            
            # Log success
            self._log_email(to_email, subject, "SUCCESS", message_id=sent_message['id'])
            return True, f"Email sent to {to_email} (ID: {sent_message['id']})"

        except HttpError as error:
            error_msg = f"An error occurred: {error}"
            self._log_email(to_email, subject, "FAILED", error_message=str(error))
            return False, error_msg
        except Exception as e:
             self._log_email(to_email, subject, "FAILED", error_message=str(e))
             return False, str(e)

    def _log_email(self, to_email, subject, status, error_message=None, message_id=None):
        """Logs email activity to DB"""
        db = SessionLocal()
        try:
            # Find contact ID if exists
            contact = db.query(EmailContact).filter(EmailContact.email == to_email).first()
            contact_id = contact.id if contact else None

            log = EmailLog(
                contact_id=contact_id,
                recipient=to_email,
                subject=subject,
                status=status,
                error_message=error_message,
                message_id=message_id
            )
            db.add(log)
            db.commit()
        except Exception as e:
            print(f"Failed to log email: {e}")
        finally:
            db.close()

    # --- Contact Management ---
    def add_contact(self, nickname, email):
        db = SessionLocal()
        try:
            # Check if exists
            existing = db.query(EmailContact).filter(EmailContact.nickname == nickname).first()
            if existing:
                return False, f"Contact '{nickname}' already exists."
            
            contact = EmailContact(nickname=nickname, email=email)
            db.add(contact)
            db.commit()
            return True, f"Contact '{nickname}' added."
        except Exception as e:
            return False, f"Error adding contact: {str(e)}"
        finally:
            db.close()

    def get_contacts(self):
        db = SessionLocal()
        try:
            contacts = db.query(EmailContact).all()
            return [{"id": c.id, "nickname": c.nickname, "email": c.email} for c in contacts]
        finally:
            db.close()

    def delete_contact(self, contact_id):
        db = SessionLocal()
        try:
            contact = db.query(EmailContact).filter(EmailContact.id == contact_id).first()
            if contact:
                db.delete(contact)
                db.commit()
                return True, "Contact deleted."
            return False, "Contact not found."
        finally:
            db.close()
            
    def get_email_by_nickname(self, nickname):
        """Case-insensitive fuzzy match for nickname"""
        db = SessionLocal()
        try:
            nickname = nickname.lower().strip()
            contacts = db.query(EmailContact).all()
            
            # Exact match
            for c in contacts:
                if c.nickname.lower() == nickname:
                    return c.email
            
            # Fuzzy / Substring
            for c in contacts:
                if nickname in c.nickname.lower():
                    return c.email
                    
            return None
        finally:
            db.close()

    def check_unread_emails(self, max_results=5):
        """Get unread emails from Inbox"""
        if not self.service: self.authenticate()
        if not self.service: return "Gmail not connected."

        try:
            results = self.service.users().messages().list(userId='me', labelIds=['INBOX', 'UNREAD'], maxResults=max_results).execute()
            messages = results.get('messages', [])

            if not messages:
                return []

            email_list = []
            for msg in messages:
                txt = self.service.users().messages().get(userId='me', id=msg['id']).execute()
                headers = txt['payload']['headers']
                subject = next((h['value'] for h in headers if h['name'] == 'Subject'), "No Subject")
                sender = next((h['value'] for h in headers if h['name'] == 'From'), "Unknown")
                snippet = txt.get('snippet', '')
                email_list.append({
                    "id": msg['id'],
                    "sender": sender,
                    "subject": subject,
                    "snippet": snippet
                })
            
            return email_list
            
        except Exception as e:
            return f"Error checking emails: {e}"
