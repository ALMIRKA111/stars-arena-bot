import asyncio
import logging
import json
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message, LabeledPrice, PreCheckoutQuery
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import LabeledPrice

# Настройки
BOT_TOKEN = "8601754069:AAEmsv40xs0M77p6Z3n0t25sJp3fpJ8a_4k"
ADMIN_ID = 8090136019
MINI_APP_URL = "https://almirka111.github.io/stars-arena-mini/"

# Инициализация
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())


# ===== КОМАНДЫ =====
@dp.message(Command("start"))
async def cmd_start(message: Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎰 Открыть игру", web_app=WebAppInfo(url=MINI_APP_URL))]
    ])
    await message.answer("Добро пожаловать! Нажми кнопку чтобы открыть игру:", reply_markup=keyboard)


@dp.message(Command("testpay"))
async def test_payment(message: Message):
    await message.answer_invoice(
        title="Тестовый платёж",
        description="Проверка работы Stars",
        payload="test_1",
        provider_token="",
        currency="XTR",
        prices=[LabeledPrice(label="Тест", amount=1)]
    )


# ===== ОБРАБОТЧИК ДАННЫХ ИЗ MINI APP =====
@dp.message(F.web_app_data)
async def handle_web_app_data(message: Message):
    data = json.loads(message.web_app_data.data)

    if data['action'] == 'deposit':
        amount = data['amount']

        await message.answer_invoice(
            title="Пополнение Stars Arena",
            description=f"Пополнение баланса на {amount} звезд",
            payload=f"deposit_{message.from_user.id}_{amount}",
            provider_token="",
            currency="XTR",
            prices=[LabeledPrice(label="Пополнение", amount=amount)]
        )


@dp.message(F.web_app_data)
async def handle_web_app_data(message: Message):
    data = json.loads(message.web_app_data.data)
    print(f"✅ Получены данные: {data}")  # ← ДОБАВЬ ЭТО

    if data['action'] == 'deposit':
        amount = data['amount']
        # ... остальной код


# ===== ПРЕДПРОВЕРКА ПЛАТЕЖА =====
@dp.pre_checkout_query()
async def pre_checkout_handler(pre_checkout_query: PreCheckoutQuery):
    await pre_checkout_query.answer(ok=True)
    print(f"✅ Платёж подтверждён: {pre_checkout_query.invoice_payload}")


# ===== УСПЕШНЫЙ ПЛАТЕЖ =====
@dp.message(F.successful_payment)
async def successful_payment_handler(message: Message):
    amount = message.successful_payment.total_amount
    await message.answer(f"✅ Спасибо! Получено {amount}⭐")


# ===== ЗАПУСК =====
async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())