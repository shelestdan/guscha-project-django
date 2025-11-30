"""Обработчик получения контактов пользователя."""

import logging
from telegram import Update
from telegram.ext import ContextTypes

from .base_handler import MessageHandler
from ..exceptions import VerificationCodeError, ValidationError

logger = logging.getLogger(__name__)


class ContactHandler(MessageHandler):
    """Обработчик получения контакта пользователя."""

    async def handle(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обрабатывает получение контакта пользователя."""
        user_info = self.get_user_info(update)
        chat_id = user_info["chat_id"]

        self.log_handler_start("contact_handler", user_info)

        # Проверяем rate limit
        await self.check_rate_limit(chat_id, "contact_sharing")

        try:
            # Получаем контакт
            contact = self.get_contact(update)
            if not contact:
                await self.message_service.send_error_message(
                    chat_id=chat_id, error_type="general"
                )
                return

            # Удаляем клавиатуру
            await self.message_service.remove_keyboard(
                chat_id=chat_id, text="📱 Номер телефона получен, проверяем..."
            )

            # Обрабатываем номер телефона
            telegram_phone = contact.phone_number
            is_valid, normalized_phone, error_msg = (
                self.phone_service.process_phone_input(
                    phone=telegram_phone, context="contact_sharing"
                )
            )

            if not is_valid:
                await self.message_service.send_simple_message(
                    chat_id=chat_id, text=f"❌ {error_msg}"
                )
                return

            # Ищем активный код верификации
            verification_code = await self._find_comprehensive_verification_code(
                chat_id
            )

            if not verification_code:
                # Если код не найден, проверяем возможность создания нового пользователя
                await self._handle_no_verification_code(
                    chat_id, normalized_phone, user_info
                )
                return

            # Проверяем, не истек ли код
            if await self.verification_service.is_expired(verification_code):
                await self.message_service.send_error_message(
                    chat_id=chat_id, error_type="code_expired"
                )
                return

            # Проверяем тип верификации
            if verification_code.verification_type == "telegram_auth":
                # Универсальный код - проверяем наличие пользователя
                await self._handle_telegram_auth(
                    verification_code=verification_code,
                    telegram_phone=normalized_phone,
                    chat_id=chat_id,
                    user_info=user_info,
                )
            else:
                # Обрабатываем другие типы верификации
                await self._handle_verification_by_type(
                    verification_code=verification_code,
                    telegram_phone=normalized_phone,
                    chat_id=chat_id,
                    user_info=user_info,
                )

            self.log_handler_success(
                "contact_handler",
                user_info,
                {
                    "verification_type": verification_code.verification_type,
                    "phone_processed": True,
                },
            )

        except Exception as e:
            await self.handle_error(update, context, e, "contact_handler")

    async def _handle_telegram_auth(
        self, verification_code, telegram_phone: str, chat_id: str, user_info: dict
    ) -> None:
        """Обрабатывает универсальную аутентификацию через Telegram."""
        try:
            # Ищем пользователя с таким номером телефона
            existing_user = await self.user_service.get_user_by_phone(telegram_phone)

            if existing_user:
                # Пользователь найден - выполняем вход
                self.logger.info(
                    f"Найден пользователь {existing_user.id} для номера {self.phone_service.get_phone_hash(telegram_phone)}"
                )

                # Обновляем telegram_chat_id если он не установлен
                if not existing_user.telegram_chat_id:
                    await self.user_service.update_telegram_info(
                        existing_user,
                        chat_id=chat_id,
                        username=user_info.get("username"),
                    )

                # Помечаем код как использованный для входа
                await self.verification_service.update_verification_code(
                    verification_code=verification_code, phone=telegram_phone
                )
                verification_code.user = existing_user
                verification_code.verification_type = (
                    "login"  # Меняем тип на login для правильной обработки на сайте
                )
                await self.verification_service.mark_as_used(verification_code)

                # Отправляем подтверждение успешного входа
                await self.message_service.send_simple_message(
                    chat_id=chat_id,
                    text=(
                        "✅ Вход выполнен успешно!\n\n"
                        f"📱 Номер: {self.phone_service.format_for_display(telegram_phone)}\n"
                        f"👤 Пользователь: {user_info.get('first_name', 'Пользователь')}\n\n"
                        "Вы можете вернуться на сайт - вход выполнен автоматически."
                    ),
                )

                self.logger.info(
                    f"Успешный вход через Telegram для пользователя {existing_user.id}"
                )

            else:
                # Пользователь не найден - предлагаем создать новый аккаунт
                self.logger.info(
                    f"Пользователь не найден для номера {self.phone_service.get_phone_hash(telegram_phone)}"
                )

                # Обновляем код верификации для регистрации
                await self.verification_service.update_verification_code(
                    verification_code=verification_code, phone=telegram_phone
                )
                verification_code.verification_type = (
                    "telegram_registration"  # Меняем тип на registration
                )
                await self.verification_service.verification_repo.save(
                    verification_code
                )

                # Отправляем запрос на подтверждение создания аккаунта
                await self.message_service.send_registration_confirmation(
                    chat_id=chat_id, phone=telegram_phone
                )

                self.logger.info(
                    f"Отправлен запрос на создание нового аккаунта для номера {self.phone_service.get_phone_hash(telegram_phone)}"
                )

        except Exception as e:
            self.logger.error(f"Ошибка обработки telegram_auth: {e}")
            await self.message_service.send_error_message(
                chat_id=chat_id, error_type="general"
            )

    async def _handle_no_verification_code(
        self, chat_id: str, phone: str, user_info: dict
    ) -> None:
        """Обрабатывает случай отсутствия кода верификации."""
        try:
            # Проверяем лимит регистрации
            if not await self.rate_limit_service.check_registration_rate_limit(chat_id):
                await self.message_service.send_error_message(
                    chat_id=chat_id, error_type="rate_limit", minutes=5
                )
                return

            # Проверяем, существует ли пользователь с таким номером
            existing_user = await self.user_service.get_user_by_phone(phone)

            if existing_user:
                # Пользователь уже существует - предлагаем войти
                await self.message_service.send_simple_message(
                    chat_id=chat_id,
                    text=(
                        f"📱 Пользователь с номером {self.phone_service.format_for_display(phone)} "
                        f"уже зарегистрирован.\n\n"
                        f"Для входа в аккаунт перейдите на сайт и выберите 'Вход через Telegram'."
                    ),
                )
                return

            # Создаем новый код верификации для регистрации через Telegram
            verification_code = (
                await self.verification_service.create_verification_code(
                    verification_type="telegram_registration",
                    chat_id=chat_id,
                    telegram_phone=phone,
                )
            )

            self.logger.info(
                f"Создан новый код верификации {verification_code.id} для регистрации через Telegram"
            )

            # Отправляем запрос на подтверждение создания аккаунта
            await self.message_service.send_registration_confirmation(
                chat_id=chat_id, phone=phone
            )

        except Exception as e:
            self.logger.error(f"Ошибка обработки отсутствия кода верификации: {e}")
            await self.message_service.send_error_message(
                chat_id=chat_id, error_type="general"
            )

    async def _handle_verification_by_type(
        self, verification_code, telegram_phone: str, chat_id: str, user_info: dict
    ) -> None:
        """Обрабатывает верификацию в зависимости от типа."""
        verification_type = verification_code.verification_type

        # Обрабатываем универсальный тип отдельно
        if verification_type == "telegram_auth":
            await self._handle_telegram_auth(
                verification_code, telegram_phone, chat_id, user_info
            )
        elif verification_type == "login":
            await self._handle_login_verification(
                verification_code, telegram_phone, chat_id
            )
        elif verification_type == "telegram_registration":
            await self._handle_telegram_registration(
                verification_code, telegram_phone, chat_id, user_info
            )
        elif verification_type == "qr_registration":
            await self._handle_qr_registration(
                verification_code, telegram_phone, chat_id
            )
        else:
            await self._handle_standard_verification(
                verification_code, telegram_phone, chat_id
            )

    async def _handle_login_verification(
        self, verification_code, telegram_phone: str, chat_id: str
    ) -> None:
        """Обрабатывает верификацию для входа."""
        if not verification_code.user:
            await self.message_service.send_error_message(
                chat_id=chat_id, error_type="no_verification_code"
            )
            return

        # Проверяем совпадение номеров
        phones_match, error_msg = await self.user_service.verify_phone_match(
            user=verification_code.user, telegram_phone=telegram_phone
        )

        if not phones_match:
            user_phone = verification_code.user.phone or "не указан"
            await self.message_service.send_error_message(
                chat_id=chat_id,
                error_type="phone_mismatch",
                telegram_phone=self.phone_service.format_for_display(telegram_phone),
                registered_phone=self.phone_service.format_for_display(user_phone),
            )
            return

        # Номера совпадают - помечаем код как использованный
        await self.verification_service.update_verification_code(
            verification_code=verification_code, phone=telegram_phone
        )
        await self.verification_service.mark_as_used(verification_code)

        # Отправляем подтверждение успешного входа
        await self.message_service.send_simple_message(
            chat_id=chat_id,
            text=(
                "✅ Вход через Telegram подтвержден!\n\n"
                "Вы можете вернуться на сайт - вход выполнен автоматически."
            ),
        )

        self.logger.info(
            f"Успешный вход через Telegram для пользователя {verification_code.user.id}"
        )

    async def _handle_telegram_registration(
        self, verification_code, telegram_phone: str, chat_id: str, user_info: dict
    ) -> None:
        """Обрабатывает регистрацию через Telegram."""
        # Сохраняем номер телефона в коде верификации
        await self.verification_service.update_verification_code(
            verification_code=verification_code, phone=telegram_phone
        )

        # Отправляем запрос на подтверждение создания аккаунта
        await self.message_service.send_registration_confirmation(
            chat_id=chat_id, phone=telegram_phone
        )

        self.logger.info(
            f"Отправлен запрос на подтверждение регистрации для номера {self.phone_service.get_phone_hash(telegram_phone)}"
        )

    async def _handle_qr_registration(
        self, verification_code, telegram_phone: str, chat_id: str
    ) -> None:
        """Обрабатывает QR-регистрацию."""
        # Проверяем номер телефона из pending_registration
        if (
            verification_code.pending_registration
            and verification_code.pending_registration.phone
        ):
            expected_phone = verification_code.pending_registration.phone
            phones_match, error_msg = self.phone_service.compare_phones(
                telegram_phone, expected_phone, "qr_registration"
            )

            if not phones_match:
                await self.message_service.send_error_message(
                    chat_id=chat_id,
                    error_type="phone_mismatch",
                    telegram_phone=self.phone_service.format_for_display(
                        telegram_phone
                    ),
                    registered_phone=self.phone_service.format_for_display(
                        expected_phone
                    ),
                )
                return

        # Сохраняем номер телефона
        await self.verification_service.update_verification_code(
            verification_code=verification_code, phone=telegram_phone
        )

        # Генерируем и отправляем код
        display_code = await self.verification_service.generate_display_code(
            verification_code
        )

        await self.message_service.send_verification_code(
            chat_id=chat_id,
            code=display_code,
            verification_type=verification_code.verification_type,
        )

        self.logger.info(f"Код {display_code} отправлен для QR-регистрации")

    async def _handle_standard_verification(
        self, verification_code, telegram_phone: str, chat_id: str
    ) -> None:
        """Обрабатывает стандартную верификацию."""
        # Проверяем совпадение номеров
        phones_match, error_msg = await self.verification_service.verify_phone_match(
            verification_code=verification_code, telegram_phone=telegram_phone
        )

        if not phones_match:
            await self.message_service.send_simple_message(
                chat_id=chat_id, text=f"❌ {error_msg}"
            )
            return

        # Сохраняем номер телефона и генерируем код
        await self.verification_service.update_verification_code(
            verification_code=verification_code, phone=telegram_phone
        )

        display_code = await self.verification_service.generate_display_code(
            verification_code
        )

        # Отправляем код пользователю
        await self.message_service.send_verification_code(
            chat_id=chat_id,
            code=display_code,
            verification_type=verification_code.verification_type,
        )

        self.logger.info(
            f"Код {display_code} отправлен пользователю {chat_id} после проверки номера телефона"
        )
