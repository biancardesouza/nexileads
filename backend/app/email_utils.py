import os
import smtplib
from email.message import EmailMessage

from dotenv import load_dotenv

load_dotenv()

SMTP_EMAIL = os.environ.get("SMTP_EMAIL")
SMTP_APP_PASSWORD = os.environ.get("SMTP_APP_PASSWORD")
FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://localhost:5173")


def enviar_email_redefinicao(destinatario: str, nome: str, token: str) -> None:
    if not SMTP_EMAIL or not SMTP_APP_PASSWORD:
        raise RuntimeError("SMTP_EMAIL/SMTP_APP_PASSWORD não configurados em backend/.env")

    link = f"{FRONTEND_URL}/?token={token}"
    msg = EmailMessage()
    msg["Subject"] = "Redefinição de senha - Faro"
    msg["From"] = SMTP_EMAIL
    msg["To"] = destinatario
    msg.set_content(
        f"Olá, {nome}!\n\n"
        "Recebemos um pedido para redefinir sua senha no Faro.\n"
        "Clique no link abaixo para criar uma nova senha (válido por 30 minutos):\n\n"
        f"{link}\n\n"
        "Se você não pediu essa redefinição, pode ignorar este e-mail."
    )

    with smtplib.SMTP("smtp.gmail.com", 587) as smtp:
        smtp.starttls()
        smtp.login(SMTP_EMAIL, SMTP_APP_PASSWORD)
        smtp.send_message(msg)
