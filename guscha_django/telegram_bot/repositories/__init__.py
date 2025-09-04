"""Репозитории для работы с данными Telegram бота."""

from .verification_code_repository import VerificationCodeRepository
from .user_repository import UserRepository
from .qr_code_repository import QRCodeRepository

__all__ = [
    'VerificationCodeRepository',
    'UserRepository', 
    'QRCodeRepository',
]