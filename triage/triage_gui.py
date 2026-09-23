from time import sleep

from email_service import EmailService
from gmail_service import GmailService
from pyperclip import copy
import pyautogui

from triage_cli import SYSTEM_PROMPT

POLL_INTERVAL_SECONDS = 5

PROMPT_TEMP = f"""{SYSTEM_PROMPT}

Do not ask any clarifying questions or any follow-up. Just use the tools and make the tickets/issues.

Following lines are the sender, subject, and body."""

email_service: EmailService = GmailService()

print(f"Watching for unread emails every {POLL_INTERVAL_SECONDS} seconds (desktop style)...")

while True:
    processed_any = False

    for unread_email in email_service:
        print(unread_email)
        try:
            # Cycle through windows (on Windows) to find Claude Desktop
            claude_focus = False
            while not claude_focus:
                sleep(1)
                try:
                    pyautogui.hotkey('alt', 'esc')
                    claude_window = pyautogui.locateOnScreen("claude_icon_dark.png", confidence=0.9)
                    if claude_window is None:
                        raise Exception()

                    pyautogui.click(x=claude_window.left, y=claude_window.top)
                    claude_focus = True
                except:
                    pass
          
            # Make and paste the prompt into Claude Desktop
            prompt = f"{PROMPT_TEMP}\n{unread_email.sender}\n{unread_email.subject}\n{unread_email.body}"
            copy(prompt)
            
            pyautogui.hotkey('ctrl', 'n')
            pyautogui.hotkey('ctrl', 'v')
            pyautogui.press('enter')

            print(f"Sent \"{unread_email.subject}\" to Claude Desktop")
            print()

            email_service.mark_as_read(unread_email)
            processed_any = True

        except Exception as e:
            # Leave the email unread so it is retried on the next poll
            print(f"Failed to triage email {unread_email.id}: {e}")
        print()

    # Check again right away if emails were handled, in case more arrived meanwhile
    if not processed_any:
        sleep(POLL_INTERVAL_SECONDS)