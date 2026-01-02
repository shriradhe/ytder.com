"""Email notification service using FastAPI-Mail."""
import logging
from typing import List, Optional
from datetime import datetime
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from pydantic import EmailStr
from sqlalchemy.orm import Session
from .database import EmailNotification, NotificationStatus
import os

logger = logging.getLogger(__name__)

# Email configuration
email_conf = ConnectionConfig(
    MAIL_USERNAME=os.getenv("MAIL_USERNAME", "your-email@example.com"),
    MAIL_PASSWORD=os.getenv("MAIL_PASSWORD", "your-password"),
    MAIL_FROM=os.getenv("MAIL_FROM", "noreply@videodownloader.com"),
    MAIL_PORT=int(os.getenv("MAIL_PORT", 587)),
    MAIL_SERVER=os.getenv("MAIL_SERVER", "smtp.gmail.com"),
    MAIL_STARTTLS=os.getenv("MAIL_STARTTLS", "True").lower() == "true",
    MAIL_SSL_TLS=os.getenv("MAIL_SSL_TLS", "False").lower() == "true",
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True
)

fastmail = FastMail(email_conf)


class EmailService:
    """Email notification service"""
    
    @staticmethod
    async def send_email(
        recipient: EmailStr,
        subject: str,
        body: str,
        html_body: Optional[str] = None,
        db: Optional[Session] = None
    ) -> bool:
        """
        Send an email and log it to database.
        
        Args:
            recipient: Email address
            subject: Email subject
            body: Plain text body
            html_body: HTML body (optional)
            db: Database session (optional)
            
        Returns:
            bool: Success status
        """
        notification_log = None
        
        # Create log entry
        if db:
            notification_log = EmailNotification(
                recipient_email=recipient,
                subject=subject,
                body=body,
                status=NotificationStatus.PENDING
            )
            db.add(notification_log)
            db.commit()
            db.refresh(notification_log)
        
        try:
            # Create message
            message = MessageSchema(
                subject=subject,
                recipients=[recipient],
                body=html_body if html_body else body,
                subtype=MessageType.html if html_body else MessageType.plain
            )
            
            # Send email
            await fastmail.send_message(message)
            
            # Update log
            if db and notification_log:
                notification_log.status = NotificationStatus.SENT
                notification_log.sent_at = datetime.utcnow()
                db.commit()
            
            logger.info(f"Email sent successfully to {recipient}")
            return True
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Failed to send email to {recipient}: {error_msg}")
            
            # Update log with error
            if db and notification_log:
                notification_log.status = NotificationStatus.FAILED
                notification_log.error_message = error_msg
                db.commit()
            
            return False
    
    @staticmethod
    async def send_download_notification(
        recipient: EmailStr,
        video_title: str,
        file_size: Optional[int],
        download_url: str,
        db: Optional[Session] = None
    ) -> bool:
        """Send notification about a successful download."""
        subject = f"Video Download: {video_title}"
        
        file_size_str = f"{file_size / (1024 * 1024):.2f} MB" if file_size else "Unknown"
        
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                          color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
                .info {{ background: white; padding: 20px; margin: 20px 0; border-radius: 8px; 
                        border-left: 4px solid #667eea; }}
                .button {{ display: inline-block; padding: 12px 30px; background: #667eea; 
                          color: white; text-decoration: none; border-radius: 5px; margin-top: 20px; }}
                .footer {{ text-align: center; margin-top: 30px; color: #888; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🎬 Video Download Complete!</h1>
                </div>
                <div class="content">
                    <p>Hello!</p>
                    <p>Your video has been successfully processed and is ready for download.</p>
                    
                    <div class="info">
                        <h3>📹 {video_title}</h3>
                        <p><strong>File Size:</strong> {file_size_str}</p>
                        <p><strong>Download Link:</strong> <a href="{download_url}">Click here to download</a></p>
                    </div>
                    
                    <p>Thank you for using our Video Downloader service!</p>
                    
                    <div class="footer">
                        <p>This is an automated notification. Please do not reply to this email.</p>
                        <p>&copy; 2025 Video Downloader. All rights reserved.</p>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
        
        plain_body = f"""
        Video Download Complete!
        
        Your video has been successfully processed.
        
        Video Title: {video_title}
        File Size: {file_size_str}
        Download Link: {download_url}
        
        Thank you for using our Video Downloader service!
        """
        
        return await EmailService.send_email(
            recipient=recipient,
            subject=subject,
            body=plain_body,
            html_body=html_body,
            db=db
        )
    
    @staticmethod
    async def send_admin_notification(
        recipient: EmailStr,
        title: str,
        message: str,
        notification_type: str = "info",
        db: Optional[Session] = None
    ) -> bool:
        """Send notification to admin user."""
        subject = f"Admin Notification: {title}"
        
        # Color based on type
        colors = {
            "info": "#2196f3",
            "success": "#4caf50",
            "warning": "#ff9800",
            "error": "#f44336"
        }
        color = colors.get(notification_type, "#2196f3")
        
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: {color}; color: white; padding: 30px; 
                          text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
                .message {{ background: white; padding: 20px; margin: 20px 0; 
                           border-radius: 8px; border-left: 4px solid {color}; }}
                .footer {{ text-align: center; margin-top: 30px; color: #888; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🔔 {title}</h1>
                </div>
                <div class="content">
                    <div class="message">
                        <p>{message}</p>
                    </div>
                    
                    <div class="footer">
                        <p>This is an automated notification from your Video Downloader admin panel.</p>
                        <p>&copy; 2025 Video Downloader. All rights reserved.</p>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
        
        plain_body = f"{title}\n\n{message}"
        
        return await EmailService.send_email(
            recipient=recipient,
            subject=subject,
            body=plain_body,
            html_body=html_body,
            db=db
        )
    
    @staticmethod
    async def send_bulk_notifications(
        recipients: List[EmailStr],
        subject: str,
        body: str,
        html_body: Optional[str] = None,
        db: Optional[Session] = None
    ) -> dict:
        """
        Send emails to multiple recipients.
        
        Returns:
            dict: {"sent": count, "failed": count}
        """
        sent = 0
        failed = 0
        
        for recipient in recipients:
            success = await EmailService.send_email(
                recipient=recipient,
                subject=subject,
                body=body,
                html_body=html_body,
                db=db
            )
            if success:
                sent += 1
            else:
                failed += 1
        
        return {"sent": sent, "failed": failed}

