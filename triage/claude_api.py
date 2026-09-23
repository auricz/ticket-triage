from email_service import EmailService
from gmail_service import GmailService

email_service: EmailService = GmailService()

for unread_email in email_service:
    print(unread_email)

    # email_service.mark_as_read(unread_email)
