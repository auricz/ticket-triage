

class Email():
    def __init__(self, sender, subject, body) -> None:
        self.sender = sender
        self.subject = subject
        self.body = body

    def __str__(self) -> str:
        return f"From: {self.sender}\nSubject: {self.subject if self.subject else "No Subject"}\n\n{self.body}"