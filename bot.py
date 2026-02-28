import asyncio
import logging
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, CommandStart
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.storage.memory import MemoryStorage

from config import config
from database import db
from keyboards import kb
from games import router as games_router
from payments import payments  # Импортируем объект payments

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Инициализация бота
bot = Bot(token=config.BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# Подключаем роутеры
dp.include_router(games_router)


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
            f"🎁 Тебе начислено 100⭐ за регистрацию!",
            parse_mode='HTML',
            reply_markup=kb.main_menu()
        )
    else:
        await message.answer(
            f"✨ <b>С возвращением, {first_name}!</b>",
            parse_mode='HTML',
            reply_markup=kb.main_menu()
        )


@dp.message(Command("menu"))
async def cmd_menu(message: Message):
    """Вернуться в меню"""
    await message.answer("🎰 Главное меню:", reply_markup=kb.main_menu())


# ===== ОБРАБОТЧИКИ КНОПОК =====
@dp.callback_query(F.data == "back_to_main")
async def back_to_main(callback: CallbackQuery):
    """Назад в главное меню"""
    await callback.message.edit_text(
        "🎰 Главное меню:",
        reply_markup=kb.main_menu()
    )
    await callback.answer()


@dp.callback_query(F.data == "profile")
async def show_profile(callback: CallbackQuery):
    """Показать профиль"""
    user = db.get_user(callback.from_user.id)

    if not user:
        await callback.answer("❌ Ошибка загрузки профиля")
        return

    text = (
        f"👤 <b>Твой профиль</b>\n\n"
        f"🆔 ID: <code>{user['telegram_id']}</code>\n"
        f"⭐ Баланс Stars: {user['stars_balance']}\n"
        f"💎 Баланс TON: {user['ton_balance']}\n"
        f"🎮 Сыграно игр: {user['games_played']}\n"
        f"🏆 Побед: {user['games_won']}\n"
        f"📊 Процент побед: {user['games_won'] / max(user['games_played'], 1) * 100:.1f}%\n"
        f"📥 Всего пополнено Stars: {user['total_deposited_stars']}\n"
        f"📤 Всего выведено Stars: {user['total_withdrawn_stars']}"
    )

    await callback.message.edit_text(
        text,
        parse_mode='HTML',
        reply_markup=kb.profile_menu()
    )
    await callback.answer()


@dp.callback_query(F.data == "balance")
async def show_balance(callback: CallbackQuery):
    """Показать баланс"""
    user = db.get_user(callback.from_user.id)

    text = (
        f"💰 <b>Твой баланс</b>\n\n"
        f"⭐ Stars: {user['stars_balance']}\n"
        f"💎 TON: {user['ton_balance']}\n\n"
        f"📥 Пополнить — 0% комиссии\n"
        f"📤 Вывести — 2% комиссии"
    )

    await callback.message.edit_text(
        text,
        parse_mode='HTML',
        reply_markup=kb.back_button("profile")
    )
    await callback.answer()


@dp.callback_query(F.data == "stats")
async def show_stats(callback: CallbackQuery):
    """Показать статистику"""
    user = db.get_user(callback.from_user.id)

    text = (
        f"📊 <b>Твоя статистика</b>\n\n"
        f"🎮 Всего игр: {user['games_played']}\n"
        f"🏆 Побед: {user['games_won']}\n"
        f"📈 Процент: {user['games_won'] / max(user['games_played'], 1) * 100:.1f}%\n"
        f"⭐ Всего выиграно Stars: {user['total_withdrawn_stars']}\n"
        f"💎 Всего выиграно TON: {user['total_withdrawn_ton']}"
    )

    await callback.message.edit_text(
        text,
        parse_mode='HTML',
        reply_markup=kb.back_button("profile")
    )
    await callback.answer()


@dp.callback_query(F.data == "deposit")
async def deposit_menu(callback: CallbackQuery):
    """Меню пополнения"""
    await callback.message.edit_text(
        "📥 <b>Пополнение баланса</b>\n\n"
        "Выбери способ пополнения:\n"
        "• ⭐ Stars — 0% комиссии\n"
        "• 💎 TON — 0% комиссии",
        parse_mode='HTML',
        reply_markup=kb.deposit_menu()
    )
    await callback.answer()


@dp.callback_query(F.data == "withdraw_menu")
async def withdraw_menu(callback: CallbackQuery):
    """Меню вывода"""
    await callback.message.edit_text(
        "📤 <b>Вывод средств</b>\n\n"
        "Выбери способ вывода:\n"
        "• ⭐ Stars — комиссия 2%\n"
        "• 💎 TON — комиссия 2%",
        parse_mode='HTML',
        reply_markup=kb.withdraw_menu()
    )
    await callback.answer()


# ===== ЗАПУСК =====
async def main():
    logger.info("🚀 Запуск бота Stars Arena...")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())