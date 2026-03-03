import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import LabeledPrice, InlineKeyboardMarkup, InlineKeyboardButton

# Вставь сюда свой токен от BotFather
API_TOKEN = '8601754069:AAEmsv40xs0M77p6Z3n0t25sJp3fpJ8a_4k'

bot = Bot(token=API_TOKEN)
dp = Dispatcher()


# 1. Стартовая кнопка "Пополнить"
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💎 Пополнить баланс", callback_data="recharge")]
    ])
    await message.answer("Добро пожаловать! Нажми на кнопку ниже, чтобы купить Звезды.", reply_markup=kb)


# 2. Выбор суммы пополнения
@dp.callback_query(F.data == "recharge")
async def select_amount(callback: types.CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⭐️ 50 звёзд", callback_data="buy_50")],
        [InlineKeyboardButton(text="⭐️ 100 звёзд", callback_data="buy_100")],
        [InlineKeyboardButton(text="⭐️ 500 звёзд", callback_data="buy_500")]
    ])
    await callback.message.edit_text("Выбери сумму пополнения:", reply_markup=kb)


# 3. Отправка счета (Invoice) при выборе суммы
@dp.callback_query(F.data.startswith("buy_"))
async def send_payment(callback: types.CallbackQuery):
    stars_count = int(callback.data.split("_")[1])

    await callback.message.answer_invoice(
        title="Пополнение баланса",
        description=f"Покупка {stars_count} звёзд для доступа к услугам RING",
        payload=f"recharge_{stars_count}",  # Внутренний ID платежа
        currency="XTR",  # Валюта: XTR (Telegram Stars)
        prices=[
            LabeledPrice(label="Звёзды", amount=stars_count)
        ],
        provider_token=""  # Для Звезд токен ВСЕГДА пустой
    )
    await callback.answer()


# 4. Подтверждение платежа (Pre-Checkout Query)
@dp.pre_checkout_query()
async def process_pre_checkout_query(pre_checkout_query: types.PreCheckoutQuery):
    await pre_checkout_query.answer(ok=True)


# 5. Обработка успешной оплаты
@dp.message(F.successful_payment)
async def process_successful_payment(message: types.Message):
    stars_bought = message.successful_payment.total_amount
    await message.answer(f"✅ Оплата прошла успешно! Вам начислено {stars_bought} звёзд.")
    # Здесь можно добавить логику записи в базу данных


async def main():
    print("Бот запущен...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())