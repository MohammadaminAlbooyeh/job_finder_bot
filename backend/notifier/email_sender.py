import os
import smtplib
import ssl
from email.message import EmailMessage
from typing import Dict, List


def send_email(
    subject: str,
    body: str,
    to_emails: List[str],
    from_email: str,
    smtp_server: str,
    smtp_port: int = 587,
    smtp_user: str = None,
    smtp_password: str = None,
):
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = from_email
    msg["To"] = ", ".join(to_emails)
    msg.set_content(body)

    context = ssl.create_default_context()

    with smtplib.SMTP(smtp_server, smtp_port, timeout=30) as server:
        server.starttls(context=context)
        if smtp_user and smtp_password:
            server.login(smtp_user, smtp_password)
        server.send_message(msg)


def notify_jobs_via_email(jobs: List[Dict], to_emails: List[str]):
    from_email = os.getenv("EMAIL_FROM")
    smtp_server = os.getenv("SMTP_SERVER")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER")
    smtp_password = os.getenv("SMTP_PASSWORD")

    if not all([from_email, smtp_server, to_emails]):
        raise ValueError("EMAIL_FROM, SMTP_SERVER, and recipient emails are required for email notifications")

    subject = f"Job Finder Bot: {len(jobs)} new job(s)"
    body_lines = []
    for job in jobs:
        body_lines.append(f"{job.get('title')} @ {job.get('company')} ({job.get('location')})")
        body_lines.append(job.get("url", ""))
        body_lines.append(job.get("summary", ""))
        body_lines.append("\n")

    body = "\n".join(body_lines).strip()

    send_email(
        subject=subject,
        body=body,
        to_emails=to_emails,
        from_email=from_email,
        smtp_server=smtp_server,
        smtp_port=smtp_port,
        smtp_user=smtp_user,
        smtp_password=smtp_password,
    )
