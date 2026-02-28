from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


class Keyboards:
    """Класс с красивыми клавиатурами"""

    @staticmethod
    def main_menu():
        """Главное меню"""
        builder = InlineKeyboardBuilder()

        # Ряд 1: Рулетки
        builder.row(
            InlineKeyboardButton(text="🎰 Рулетка (⭐ Stars)", callback_data="roulette_stars"),
            InlineKeyboardButton(text="💎 Рулетка (TON)", callback_data="roulette_ton"),
            width=2
        )

        # Ряд 2: Профиль
        builder.row(
            InlineKeyboardButton(text="👤 Мой профиль", callback_data="profile"),
            width=1
        )

        # Ряд 3: Пополнение и вывод
        builder.row(
            InlineKeyboardButton(text="📥 Пополнить", callback_data="deposit"),
            InlineKeyboardButton(text="📤 Вывести", callback_data="withdraw_menu"),
            width=2
        )

        # Ряд 4: Партнерская программа и промокод
        builder.row(
            InlineKeyboardButton(text="👥 Партнерская программа", callback_data="referrals"),
            InlineKeyboardButton(text="🎁 Промокод", callback_data="promo"),
            width=2
        )

        return builder.as_markup()

    @staticmethod
    def profile_menu():
        """Меню профиля"""
        builder = InlineKeyboardBuilder()

        builder.row(
            InlineKeyboardButton(text="💰 Баланс", callback_data="balance"),
            InlineKeyboardButton(text="📊 Статистика", callback_data="stats"),
            width=2
        )

        builder.row(
            InlineKeyboardButton(text="📥 Пополнить", callback_data="deposit"),
            InlineKeyboardButton(text="📤 Вывести", callback_data="withdraw_menu"),
            width=2
        )

        builder.row(
            InlineKeyboardButton(text="👥 Партнерская программа", callback_data="referrals"),
            width=1
        )

        builder.row(
            InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_main"),
            width=1
        )

        return builder.as_markup()

    @staticmethod
    def deposit_menu():
        """Меню пополнения"""
        builder = InlineKeyboardBuilder()

        # Stars
        builder.row(
            InlineKeyboardButton(text="⭐ Пополнить Stars", callback_data="deposit_stars"),
            width=1
        )

        # TON
        builder.row(
            InlineKeyboardButton(text="💎 Пополнить TON", callback_data="deposit_ton"),
            width=1
        )

        builder.row(
            InlineKeyboardButton(text="◀️ Назад", callback_data="profile"),
            width=1
        )

        return builder.as_markup()

    @staticmethod
    def withdraw_menu():
        """Меню вывода"""
        builder = InlineKeyboardBuilder()

        builder.row(
            InlineKeyboardButton(text="⭐ Вывести Stars", callback_data="withdraw_stars"),
            InlineKeyboardButton(text="💎 Вывести TON", callback_data="withdraw_ton"),
            width=2
        )

        builder.row(
            InlineKeyboardButton(text="📋 Мои заявки", callback_data="my_withdrawals"),
            width=1
        )

        builder.row(
            InlineKeyboardButton(text="◀️ Назад", callback_data="profile"),
            width=1
        )

        return builder.as_markup()

    @staticmethod
    def back_button(callback: str = "back_to_main"):
        """Кнопка назад"""
        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(text="◀️ Назад", callback_data=callback),
            width=1
        )
        return builder.as_markup()


# Создаем глобальный объект
kb = Keyboards()