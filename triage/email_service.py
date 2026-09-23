from abc import ABC, abstractmethod
from collections.abc import Iterable

class Email():
    def __init__(self, sender, subject, body, id=None) -> None:
        self.sender = sender
        self.subject = subject
        self.body = body
        self.id = id

    def __str__(self) -> str:
        return f"From: {self.sender}\nSubject: {self.subject if self.subject else "No Subject"}"
    
class EmailService(Iterable):
    @abstractmethod
    def mark_as_read(self, email: Email):
        pass