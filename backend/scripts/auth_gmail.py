import os
import sys

# Ensure backend path is in sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from automation.gmail_service import GmailService

def main():
    print("--- Gmail Authentication Script ---")
    print("This script will open your browser to authenticate with Google.")
    print("Ensure 'credentials.json' is in the 'backend' folder.\n")

    # Delete stale / revoked token so we force a clean OAuth flow
    token_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'token.json')
    if os.path.exists(token_path):
        os.remove(token_path)
        print("Removed old token.json — starting fresh auth.\n")

    # Create service (silent load — will find no token)
    auth_service = GmailService()
    # Now trigger full browser OAuth flow
    auth_service.authenticate()

    if auth_service.service:
        print("\nSUCCESS: Authentication successful! 'token.json' has been created.")
    else:
        print("\nFAILURE: Could not authenticate. Please check 'credentials.json' and try again.")

if __name__ == "__main__":
    main()
