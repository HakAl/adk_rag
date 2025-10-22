import httpx
from typing import Optional
from config import settings, logger


class EmailService:
    """Service for sending emails via Resend API."""

    def __init__(self):
        self.api_key = settings.resend_api_key
        self.from_email = "noreply@vibecoder.buzz"  # Custom verified domain
        self.from_name = "VIBE Code App Team"
        self.base_url = "https://api.resend.com"

    async def send_verification_email(
        self,
        to_email: str,
        username: str,
        verification_token: str
    ) -> bool:
        """
        Send email verification link.

        Args:
            to_email: Recipient email address
            username: User's username
            verification_token: Verification token (plain text, not hashed)

        Returns:
            True if sent successfully, False otherwise
        """
        verification_url = f"{settings.backend_url}/verify-email?token={verification_token}"

        # In development mode, log the verification URL and skip actual email sending
        if settings.environment == "development":
            logger.info("=" * 80)
            logger.info("📧 EMAIL VERIFICATION (Development Mode)")
            logger.info("=" * 80)
            logger.info(f"To: {to_email}")
            logger.info(f"Username: {username}")
            logger.info(f"🔗 Verification URL:")
            logger.info(f"   {verification_url}")
            logger.info("=" * 80)
            logger.info("Copy the URL above and paste it in your browser to verify the email.")
            logger.info("=" * 80)
            return True

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .button {{ 
                    display: inline-block; 
                    padding: 12px 24px; 
                    background-color: #007bff; 
                    color: white; 
                    text-decoration: none; 
                    border-radius: 5px;
                    margin: 20px 0;
                }}
                .footer {{ margin-top: 30px; font-size: 12px; color: #666; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h2>Welcome to VIBE Code App, {username}!</h2>
                <p>Thanks for signing up. Please verify your email address to get started.</p>
                <a href="{verification_url}" class="button">Verify Email Address</a>
                <p>Or copy and paste this link into your browser:</p>
                <p style="word-break: break-all; color: #007bff;">{verification_url}</p>
                <p>This link will expire in 24 hours.</p>
                <div class="footer">
                    <p>If you didn't create an account, you can safely ignore this email.</p>
                </div>
            </div>
        </body>
        </html>
        """

        text_content = f"""
        Welcome to VIBE Code App, {username}!

        Thanks for signing up. Please verify your email address to get started.

        Click this link to verify: {verification_url}

        This link will expire in 24 hours.

        If you didn't create an account, you can safely ignore this email.
        """

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/emails",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "from": f"{self.from_name} <{self.from_email}>",
                        "to": [to_email],
                        "subject": "Verify your email address",
                        "html": html_content,
                        "text": text_content
                    },
                    timeout=10.0
                )

                if response.status_code == 200:
                    logger.info(f"Verification email sent to {to_email}")
                    return True
                else:
                    logger.error(f"Failed to send email to {to_email}: {response.status_code} - {response.text}")
                    return False

        except Exception as e:
            logger.error(f"Error sending verification email to {to_email}: {e}", exc_info=True)
            return False


# Singleton instance
_email_service: Optional[EmailService] = None


def get_email_service() -> EmailService:
    """Get or create email service singleton."""
    global _email_service
    if _email_service is None:
        _email_service = EmailService()
    return _email_service