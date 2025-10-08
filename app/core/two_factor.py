"""
Two-Factor Authentication (2FA)
TOTP-based 2FA using authenticator apps
"""
import pyotp
import qrcode
import io
import base64
from typing import Tuple, List
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class TwoFactorAuth:
    """Two-Factor Authentication Manager"""

    @staticmethod
    def generate_secret() -> str:
        """
        Generate a new TOTP secret

        Returns:
            Base32 encoded secret
        """
        return pyotp.random_base32()

    @staticmethod
    def get_provisioning_uri(secret: str, user_email: str, issuer: str = "CyclSales") -> str:
        """
        Generate provisioning URI for QR code

        Args:
            secret: TOTP secret
            user_email: User's email
            issuer: App name

        Returns:
            otpauth:// URI
        """
        totp = pyotp.TOTP(secret)
        return totp.provisioning_uri(name=user_email, issuer_name=issuer)

    @staticmethod
    def generate_qr_code(uri: str) -> str:
        """
        Generate QR code image from provisioning URI

        Args:
            uri: Provisioning URI

        Returns:
            Base64 encoded PNG image
        """
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(uri)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")

        # Convert to base64
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)
        img_base64 = base64.b64encode(buffer.getvalue()).decode()

        return f"data:image/png;base64,{img_base64}"

    @staticmethod
    def verify_token(secret: str, token: str) -> bool:
        """
        Verify a TOTP token

        Args:
            secret: TOTP secret
            token: 6-digit code from authenticator app

        Returns:
            True if valid
        """
        totp = pyotp.TOTP(secret)
        return totp.verify(token, valid_window=1)  # Allow 30s clock skew

    @staticmethod
    def generate_backup_codes(count: int = 10) -> Tuple[List[str], List[str]]:
        """
        Generate backup codes for recovery

        Args:
            count: Number of codes to generate

        Returns:
            Tuple of (plain_codes, hashed_codes)
        """
        import secrets

        plain_codes = []
        hashed_codes = []

        for _ in range(count):
            # Generate 8-character alphanumeric code
            code = ''.join(secrets.choice('ABCDEFGHJKLMNPQRSTUVWXYZ23456789') for _ in range(8))
            plain_codes.append(code)
            hashed_codes.append(pwd_context.hash(code))

        return plain_codes, hashed_codes

    @staticmethod
    def verify_backup_code(code: str, hashed_codes: List[str]) -> Tuple[bool, int]:
        """
        Verify a backup code

        Args:
            code: Plain backup code
            hashed_codes: List of hashed codes

        Returns:
            Tuple of (is_valid, index_if_valid)
        """
        for index, hashed in enumerate(hashed_codes):
            if pwd_context.verify(code, hashed):
                return True, index
        return False, -1

    @staticmethod
    def setup_2fa(user_email: str) -> dict:
        """
        Complete 2FA setup for a user

        Args:
            user_email: User's email

        Returns:
            Dict with secret, QR code, and backup codes
        """
        # Generate secret
        secret = TwoFactorAuth.generate_secret()

        # Generate QR code
        uri = TwoFactorAuth.get_provisioning_uri(secret, user_email)
        qr_code = TwoFactorAuth.generate_qr_code(uri)

        # Generate backup codes
        plain_codes, hashed_codes = TwoFactorAuth.generate_backup_codes()

        return {
            "secret": secret,
            "qr_code": qr_code,
            "provisioning_uri": uri,
            "backup_codes": plain_codes,
            "backup_codes_hashed": hashed_codes,
        }


# Singleton instance
two_factor_auth = TwoFactorAuth()
