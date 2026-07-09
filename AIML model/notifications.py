"""
Notification Alerts — Email/Webhook notification system.

Sends alerts when new job notifications are detected.
Supports email (SMTP) and webhook (HTTP POST) delivery.
"""

import os
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import Dict, List, Optional

import requests


class NotificationService:
    """Service for sending job notification alerts."""

    def __init__(self):
        self.smtp_host = os.getenv('SMTP_HOST', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.smtp_user = os.getenv('SMTP_USER', '')
        self.smtp_pass = os.getenv('SMTP_PASS', '')
        self.from_email = os.getenv('FROM_EMAIL', self.smtp_user)
        self.webhook_url = os.getenv('WEBHOOK_URL', '')
        self.alert_emails = os.getenv('ALERT_EMAILS', '').split(',')
        self.enabled = bool(self.smtp_user or self.webhook_url)

    def notify_new_jobs(self, jobs: List[Dict]):
        """Send notifications for newly discovered job listings."""
        if not self.enabled or not jobs:
            return

        subject = f"🔔 {len(jobs)} New Government Job Notifications Found"
        body = self._format_job_alert(jobs)

        # Send email
        if self.smtp_user and self.alert_emails:
            for email in self.alert_emails:
                email = email.strip()
                if email:
                    try:
                        self._send_email(email, subject, body)
                    except Exception as e:
                        print(f"  ⚠️ Email to {email} failed: {e}")

        # Send webhook
        if self.webhook_url:
            try:
                self._send_webhook(jobs)
            except Exception as e:
                print(f"  ⚠️ Webhook failed: {e}")

    def _format_job_alert(self, jobs: List[Dict]) -> str:
        """Format jobs list as an HTML email body."""
        html = f"""
        <html>
        <head><style>
            body {{ font-family: 'Segoe UI', Arial, sans-serif; background: #f5f5f5; padding: 20px; }}
            .card {{ background: white; border-radius: 8px; padding: 16px; margin: 12px 0;
                     box-shadow: 0 2px 4px rgba(0,0,0,0.1); border-left: 4px solid #1a73e8; }}
            .org {{ color: #1a73e8; font-size: 12px; text-transform: uppercase; letter-spacing: 1px; }}
            .title {{ font-size: 16px; font-weight: 600; color: #202124; margin: 4px 0; }}
            .meta {{ color: #5f6368; font-size: 13px; }}
            .badge {{ display: inline-block; background: #e8f0fe; color: #1a73e8; padding: 2px 8px;
                      border-radius: 4px; font-size: 11px; margin: 2px; }}
            .header {{ text-align: center; padding: 20px; }}
            .header h1 {{ color: #1a73e8; margin: 0; }}
            .footer {{ text-align: center; color: #9aa0a6; font-size: 12px; padding: 20px; }}
        </style></head>
        <body>
        <div class="header">
            <h1>🏛️ GovTechJobs Alert</h1>
            <p style="color:#5f6368;">{len(jobs)} new notifications found on {datetime.now().strftime('%d %B %Y')}</p>
        </div>
        """

        for job in jobs[:20]:  # Limit to 20 jobs per email
            vacancies = job.get('vacancies', 'N/A')
            last_date = job.get('application_last_date', 'Check portal')
            org = job.get('organization', 'Unknown')
            title = job.get('exam_name', job.get('post_name', 'Notification'))
            qualification = job.get('qualification', 'As per notification')
            apply_link = job.get('apply_link', '#')

            html += f"""
            <div class="card">
                <div class="org">{org} — {job.get('organization_full', '')}</div>
                <div class="title">{title}</div>
                <div class="meta">
                    <span class="badge">📋 {vacancies} vacancies</span>
                    <span class="badge">📅 Last Date: {last_date}</span>
                    <span class="badge">🎯 {job.get('job_domain', 'General')}</span>
                </div>
                <div class="meta" style="margin-top:8px;">
                    Qualification: {qualification[:100]}
                </div>
                <div style="margin-top:8px;">
                    <a href="{apply_link}" style="color:#1a73e8; text-decoration:none;">
                        Apply Now →
                    </a>
                </div>
            </div>
            """

        html += """
        <div class="footer">
            <p>Sent by GovTechJobs AI — Powered by ML Ensemble</p>
        </div>
        </body></html>
        """

        return html

    def _send_email(self, to_email: str, subject: str, html_body: str):
        """Send an email via SMTP."""
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = self.from_email
        msg['To'] = to_email
        msg.attach(MIMEText(html_body, 'html'))

        with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
            server.starttls()
            server.login(self.smtp_user, self.smtp_pass)
            server.send_message(msg)

        print(f"  ✅ Email sent to {to_email}")

    def _send_webhook(self, jobs: List[Dict]):
        """Send job data via webhook (HTTP POST)."""
        payload = {
            'event': 'new_jobs_found',
            'timestamp': datetime.now().isoformat(),
            'count': len(jobs),
            'jobs': jobs[:50],  # Limit payload size
        }

        response = requests.post(
            self.webhook_url,
            json=payload,
            headers={'Content-Type': 'application/json'},
            timeout=10,
        )
        response.raise_for_status()
        print(f"  ✅ Webhook sent ({response.status_code})")


# Singleton instance
notification_service = NotificationService()
