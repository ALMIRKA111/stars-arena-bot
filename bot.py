import asyncio
import logging
import sqlite3
import json
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, CommandStart
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, LabeledPrice, \
    PreCheckoutQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

from config import config
from database import db
from keyboards import kb
from games import router as games_router
from payments import payments

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Инициализация бота
bot = Bot(token=config.BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# Подключаем роутеры
dp.include_router(games_router)


# ===== СОСТОЯНИЯ =====
class DepositStates(StatesGroup):
    waiting_for_amount = State()


# ===== КОМАНДЫ =====
@dp.message(CommandStart())
async def cmd_start(message: Message):
    """Обработчик команды /start"""
    telegram_id = message.from_user.id
    username = message.from_user.username
    first_name = message.from_user.first_name

    # Проверяем реферальный код
    referrer_id = None
    if message.text and len(message.text.split()) > 1:
        ref_arg = message.text.split()[1]
        if ref_arg.startswith('ref_'):
            try:
                referrer_telegram_id = int(ref_arg.replace('ref_', ''))
                referrer = db.get_user(referrer_telegram_id)
                if referrer:
                    referrer_id = referrer['id']
            except:
                pass

    # Получаем или создаем пользователя
    user = db.get_user(telegram_id)
    if not user:
        user = db.create_user(telegram_id, username, first_name, referrer_id)
        await message.answer(
            f"✨ <b>Добро пожаловать в {config.BOT_NAME}!</b>\n\n"
            f"{config.BOT_DESCRIPTION}\n\n"
            f"🎁 Тебе начислено 0⭐ за регистрацию!\n\n"
            f"👇 Нажми кнопку чтобы открыть игру:",
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🎮 Открыть игру", web_app=config.MINI_APP_URL)]
            ])
        )
    else:
        await message.answer(
            f"✨ <b>С возвращением, {first_name}!</b>\n\n"
            f"👇 Нажми кнопку чтобы открыть игру:",
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🎮 Открыть игру", web_app=config.MINI_APP_URL)]
            ])
        )


# ===== ПОПОЛНЕНИЕ ЧЕРЕЗ STARS =====
@dp.message(Command("deposit"))
async def cmd_deposit(message: Message):
    """Команда для пополнения"""
    await message.answer(
        "💎 <b>Пополнение баланса</b>\n\n"
        "Введи сумму в звездах (минимум 10⭐):",
        parse_mode='HTML'
    )
    await DepositStates.waiting_for_amount.set()


@dp.message(DepositStates.waiting_for_amount)
async def process_deposit_amount(message: Message, state: FSMContext):
    """Обработка введенной суммы"""
    try:
        amount = int(message.text)
    except ValueError:
        await message.answer("❌ Пожалуйста, введи целое число")
        return

    if amount < 10:
        await message.answer("❌ Минимальная сумма: 10⭐. Введи другую сумму:")
        return

    # Создаем счет в Telegram Stars
    prices = [LabeledPrice(label="Пополнение баланса", amount=amount)]

    await bot.send_invoice(
        chat_id=message.chat.id,
        title="Пополнение баланса",
        description=f"Пополнение игрового счета на {amount} звезд",
        payload=f"deposit_{message.from_user.id}_{amount}",
        provider_token="",  # Пусто для Stars
        currency="XTR",
        prices=prices,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=f"💳 Оплатить {amount} ⭐", pay=True)]
        ])
    )

    await state.clear()


# ===== ПРЕДПРОВЕРКА ПЛАТЕЖА =====
@dp.pre_checkout_query()
async def pre_checkout_handler(pre_checkout_query: PreCheckoutQuery):
    """Подтверждение платежа"""
    await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)
    logger.info(f"✅ Платеж подтвержден: {pre_checkout_query.invoice_payload}")


# ===== УСПЕШНЫЙ ПЛАТЕЖ =====
@dp.message(F.successful_payment)
async def successful_payment_handler(message: Message):
    """Обработка успешного платежа"""
    payment = message.successful_payment
    payload = payment.invoice_payload
    amount = payment.total_amount

    # Парсим payload
    parts = payload.split('_')
    user_id = int(parts[1])

    # Зачисляем звезды
    success = db.add_stars(user_id, amount, 'deposit')

    if success:
        user = db.get_user(user_id)
        await message.answer(
            f"✅ <b>Пополнение успешно!</b>\n\n"
            f"На твой счет зачислено: <b>{amount}⭐</b>\n"
            f"Текущий баланс: {user['stars_balance']}⭐\n\n"
            f"Ты можешь продолжить игру через /start",
            parse_mode='HTML'
        )

        # Уведомление админу
        await bot.send_message(
            chat_id=config.ADMIN_ID,
            text=(
                f"💰 <b>Новый платеж!</b>\n\n"
                f"👤 Пользователь: @{user['username'] or 'нет'}\n"
                f"💎 Сумма: {amount}⭐\n"
                f"🆔 ID: {user_id}"
            ),
            parse_mode='HTML'
        )
    else:
        await message.answer(
            "❌ Ошибка при зачислении средств. Обратись в поддержку.",
            parse_mode='HTML'
        )


# ===== ЗАПУСК =====
async def main():
    logger.info("🚀 Запуск бота Stars Arena...")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())