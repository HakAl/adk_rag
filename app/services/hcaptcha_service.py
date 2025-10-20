import aiohttp
from typing import Tuple, Optional
from config import settings, logger


class HCaptchaService:
    """Service for verifying hCaptcha tokens."""

    VERIFY_URL = "https://hcaptcha.com/siteverify"

    async def verify_token(self, token: str, client_ip: Optional[str] = None) -> Tuple[bool, Optional[str]]:
        """
        Verify hCaptcha token with hCaptcha API.

        Args:
            token: hCaptcha response token from frontend
            client_ip: Optional client IP address

        Returns:
            Tuple of (success: bool, error_message: Optional[str])
        """
        if not settings.hcaptcha_secret_key:
            logger.error("hCaptcha secret key not configured")
            return False, "CAPTCHA verification not configured"

        payload = {
            "secret": settings.hcaptcha_secret_key,
            "response": token
        }

        if client_ip:
            payload["remoteip"] = client_ip

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                        self.VERIFY_URL,
                        data=payload,
                        timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status != 200:
                        logger.error(f"hCaptcha API error: {response.status}")
                        return False, "CAPTCHA verification failed"

                    result = await response.json()

                    if result.get("success"):
                        return True, None

                    # Log error codes for debugging
                    error_codes = result.get("error-codes", [])
                    logger.warning(f"hCaptcha verification failed: {error_codes}")

                    # Provide user-friendly error messages
                    if "missing-input-response" in error_codes:
                        return False, "CAPTCHA response missing"
                    elif "invalid-input-response" in error_codes:
                        return False, "Invalid CAPTCHA response"
                    elif "timeout-or-duplicate" in error_codes:
                        return False, "CAPTCHA expired or already used"
                    else:
                        return False, "CAPTCHA verification failed"

        except aiohttp.ClientError as e:
            logger.error(f"hCaptcha API request failed: {e}")
            return False, "CAPTCHA verification service unavailable"
        except Exception as e:
            logger.error(f"Unexpected error verifying hCaptcha: {e}")
            return False, "CAPTCHA verification error"