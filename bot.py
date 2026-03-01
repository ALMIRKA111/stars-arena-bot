import asyncio
import logging
import json
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, CommandStart
from aiogram.types import (
    Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton,
    LabeledPrice, PreCheckoutQuery, WebAppInfo
)
from aiogram.fsm.storage.memory import MemoryStorage

# Настройки
BOT_TOKEN = "8601754069:AAEmsv40xs0M77p6Z3n0t25sJp3fpJ8a_4k"
ADMIN_ID = 8090136019  # Твой Telegram ID
MINI_APP_URL = "https://almirka111.github.io/stars-arena-mini/"

# Инициализация
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())


# ===== КОМАНДЫ =====
@dp.message(CommandStart())
async def cmd_start(message: Message):
    """Старт"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎰 Открыть игру", web_app=WebAppInfo(url=MINI_APP_URL))],
        [InlineKeyboardButton(text="👤 Профиль", callback_data="profile")]
    ])

    await message.answer(
        f"✨ Добро пожаловать, {message.from_user.first_name}!\n\n"
        f"👇 Нажми кнопку чтобы открыть игру:",
        reply_markup=keyboard
    )


# ===== ОБРАБОТЧИК ИЗ MINI APP =====
@dp.message(F.web_app_data)
async def handle_web_app_data(message: Message):
    """Получаем данные из Mini App"""
    data = json.loads(message.web_app_data.data)

    if data['action'] == 'deposit':
        amount = data['amount']

        # Проверка
        if amount < 10:
            await message.answer("❌ Минимальная сумма 10⭐")
            return

        # СОЗДАЁМ СЧЁТ (ТОЧНО КАК НА ФОТО)
        prices = [LabeledPrice(label="Пополнение баланса Stars Arena", amount=amount)]

        await bot.send_invoice(
            chat_id=message.chat.id,
            title="Пополнение баланса",
            description=f"Пополнение игрового счета на {amount} звезд",
            payload=f"deposit_{message.from_user.id}_{amount}",
            provider_token="",  # Пусто для Stars
            currency="XTR",
            prices=prices,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text=f"💳 Подтвердить и заплатить {amount} ⭐", pay=True)]
            ])
        )


# ===== ПРЕДПРОВЕРКА =====
@dp.pre_checkout_query()
async def pre_checkout_handler(pre_checkout_query: PreCheckoutQuery):
    """Обязательно подтверждаем платеж"""
    await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)


# ===== УСПЕШНЫЙ ПЛАТЕЖ =====
@dp.message(F.successful_payment)
async def successful_payment_handler(message: Message):
    """Зачисляем звёзды"""
    payment = message.successful_payment
    amount = payment.total_amount

    # Здесь твоя функция добавления в БД
    # await db.add_stars(message.from_user.id, amount)

    await message.answer(
        f"✅ Пополнено {amount}⭐!\n"
        f"Можешь продолжать игру через /start"
    )


# ===== ПРОФИЛЬ =====
@dp.callback_query(F.data == "profile")
async def show_profile(callback: CallbackQuery):
    """Профиль"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⭐ Пополнить", callback_data="deposit")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="back")]
    ])

    await callback.message.edit_text(
        f"👤 Профиль\n\n"
        f"ID: {callback.from_user.id}\n"
        f"Баланс: 0⭐\n\n"
        f"Пополни баланс чтобы играть!",
        reply_markup=keyboard
    )


@dp.callback_query(F.data == "deposit")
async def deposit_info(callback: CallbackQuery):
    """Инструкция по пополнению"""
    await callback.message.edit_text(
        "💎 Пополнение через Telegram Stars\n\n"
        "1️⃣ Открой игру\n"
        "2️⃣ Нажми 'Пополнить'\n"
        "3️⃣ Введи сумму (от 10⭐)\n"
        "4️⃣ Подтверди платёж\n\n"
        "Средства зачисляются мгновенно!",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🎰 Открыть игру", web_app=WebAppInfo(url=MINI_APP_URL))],
            [InlineKeyboardButton(text="◀️ Назад", callback_data="profile")]
        ])
    )


@dp.callback_query(F.data == "back")
async def back_to_main(callback: CallbackQuery):
    """Назад"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎰 Открыть игру", web_app=WebAppInfo(url=MINI_APP_URL))],
        [InlineKeyboardButton(text="👤 Профиль", callback_data="profile")]
    ])
    await callback.message.edit_text("Главное меню:", reply_markup=keyboard)


# ===== ЗАПУСК =====
async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
