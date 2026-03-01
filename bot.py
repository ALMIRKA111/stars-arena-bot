import asyncio
import logging
import sqlite3
import json
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, CommandStart
from aiogram.types import (
    Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton,
    LabeledPrice, PreCheckoutQuery, WebAppInfo
)
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

# URL Mini App
MINI_APP_URL = "https://almirka111.github.io/stars-arena-mini/"


# ===== СОСТОЯНИЯ =====
class WithdrawStates(StatesGroup):
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
        welcome_text = (
            f"✨ <b>Добро пожаловать в {config.BOT_NAME}!</b>\n\n"
            f"🎰 Уникальная рулетка с 15 цветами\n"
            f"💎 Реальные ставки на Telegram Stars\n"
            f"👥 Партнерская программа 10%\n\n"
            f"👇 Нажми кнопку, чтобы открыть игру:"
        )
    else:
        welcome_text = (
            f"✨ <b>С возвращением, {first_name}!</b>\n\n"
            f"👇 Нажми кнопку, чтобы открыть игру:"
        )

    # Создаем кнопку для открытия Mini App
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎰 Открыть Stars Arena", web_app=WebAppInfo(url=MINI_APP_URL))],
        [InlineKeyboardButton(text="👤 Мой профиль", callback_data="profile")],
        [InlineKeyboardButton(text="📊 Правила игры", callback_data="rules")]
    ])

    await message.answer(welcome_text, parse_mode='HTML', reply_markup=keyboard)


@dp.message(Command("menu"))
async def cmd_menu(message: Message):
    """Вернуться в меню"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎰 Открыть Stars Arena", web_app=WebAppInfo(url=MINI_APP_URL))],
        [InlineKeyboardButton(text="👤 Мой профиль", callback_data="profile")],
        [InlineKeyboardButton(text="📊 Правила игры", callback_data="rules")]
    ])
    await message.answer("🎰 Главное меню:", reply_markup=keyboard)


# ===== ОБРАБОТЧИК ДАННЫХ ИЗ MINI APP =====
@dp.message(F.web_app_data)
async def handle_web_app_data(message: Message):
    """Обработка данных из Mini App"""
    import json
    from aiogram.types import LabeledPrice, InlineKeyboardMarkup, InlineKeyboardButton

    data = json.loads(message.web_app_data.data)

    if data['action'] == 'deposit':
        amount = data['amount']

        # Проверяем минимальную сумму
        if amount < 10:
            await message.answer("❌ Минимальная сумма пополнения: 10⭐")
            return

        # Создаём счёт в Telegram Stars
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
                [InlineKeyboardButton(text=f"💳 Оплатить {amount} ⭐", pay=True)]
            ])
        )


# ===== ОБРАБОТЧИКИ КНОПОК =====
@dp.callback_query(F.data == "profile")
async def show_profile(callback: CallbackQuery):
    """Показать профиль"""
    user = db.get_user(callback.from_user.id)

    if not user:
        await callback.answer("❌ Ошибка загрузки профиля")
        return

    winnable = db.get_winnable_balance(callback.from_user.id)
    deposited = db.get_deposit_balance(callback.from_user.id)

    text = (
        f"👤 <b>Твой профиль</b>\n\n"
        f"🆔 ID: <code>{user['telegram_id']}</code>\n\n"
        f"💰 <b>Баланс:</b>\n"
        f"• Всего: {user['stars_balance']}⭐\n"
        f"• Выиграно (можно вывести): {winnable}⭐\n"
        f"• Внесено (не выводится): {deposited}⭐\n\n"
        f"🎮 Сыграно игр: {user['games_played']}\n"
        f"🏆 Побед: {user['games_won']}\n"
        f"📊 Процент: {user['games_won'] / max(user['games_played'], 1) * 100:.1f}%\n\n"
        f"📥 Пополнение: 0% комиссии\n"
        f"📤 Вывод: 2% комиссии (от 1000⭐)"
    )

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⭐ Пополнить через Stars", callback_data="start_deposit")],
        [InlineKeyboardButton(text="💸 Вывести", callback_data="withdraw_menu")],
        [InlineKeyboardButton(text="👥 Партнерская программа", callback_data="partner")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_main")]
    ])

    await callback.message.edit_text(text, parse_mode='HTML', reply_markup=keyboard)
    await callback.answer()


@dp.callback_query(F.data == "rules")
async def show_rules(callback: CallbackQuery):
    """Показать правила игры"""
    text = (
        "📋 <b>Правила игры в Stars Arena</b>\n\n"
        "🎯 <b>Как играть:</b>\n"
        "• Выбери сумму ставки (от 1⭐)\n"
        "• Тебе случайно выпадает один из 15 цветов\n"
        "• Твой процент = твоя ставка / общий банк\n"
        "• Победитель выбирается случайно, но с учетом процентов\n\n"
        "💰 <b>Пополнение:</b>\n"
        "• Через Telegram Stars, комиссия 0%\n"
        "• Минимальная сумма: 10⭐\n\n"
        "💸 <b>Вывод:</b>\n"
        "• Только выигранные звезды\n"
        "• Минимальная сумма: 1000⭐\n"
        "• Комиссия: 2%\n\n"
        "👥 <b>Партнерская программа:</b>\n"
        "• 10% от всех ставок твоих рефералов\n"
        "• Вывод от 150⭐"
    )

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_main")]
    ])

    await callback.message.edit_text(text, parse_mode='HTML', reply_markup=keyboard)
    await callback.answer()


@dp.callback_query(F.data == "back_to_main")
async def back_to_main(callback: CallbackQuery):
    """Назад в главное меню"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎰 Открыть Stars Arena", web_app=WebAppInfo(url=MINI_APP_URL))],
        [InlineKeyboardButton(text="👤 Мой профиль", callback_data="profile")],
        [InlineKeyboardButton(text="📊 Правила игры", callback_data="rules")]
    ])
    await callback.message.edit_text("🎰 Главное меню:", reply_markup=keyboard)
    await callback.answer()


@dp.callback_query(F.data == "start_deposit")
async def start_deposit(callback: CallbackQuery):
    """Начать пополнение"""
    text = (
        "💎 <b>Пополнение через Telegram Stars</b>\n\n"
        "Просто отправь мне сумму цифрами (от 10⭐)\n"
        "Например: 50\n\n"
        "После этого я пришлю тебе счет для оплаты."
    )

    await callback.message.edit_text(text, parse_mode='HTML')
    await callback.answer()


# ===== ПЛАТЕЖИ =====
@dp.pre_checkout_query()
async def pre_checkout_handler(pre_checkout_query: PreCheckoutQuery):
    """Подтверждение платежа"""
    await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)
    logger.info(f"✅ Платеж подтвержден: {pre_checkout_query.invoice_payload}")


@dp.message(F.successful_payment)
async def successful_payment_handler(message: Message):
    """Обработка успешного платежа"""
    payment = message.successful_payment
    payload = payment.invoice_payload
    amount = payment.total_amount

    # Парсим payload (формат: deposit_userid_amount)
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
            f"Ты можешь продолжить игру через /menu",
            parse_mode='HTML'
        )

        # Уведомление админу
        try:
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
        except:
            pass
    else:
        await message.answer(
            "❌ Ошибка при зачислении средств. Обратись в поддержку.",
            parse_mode='HTML'
        )


# ===== ВЫВОД СРЕДСТВ =====
@dp.callback_query(F.data == "withdraw_menu")
async def withdraw_menu(callback: CallbackQuery):
    """Меню вывода"""
    user = db.get_user(callback.from_user.id)
    winnable = db.get_winnable_balance(callback.from_user.id)
    deposited = db.get_deposit_balance(callback.from_user.id)

    text = (
        f"📤 <b>Вывод средств</b>\n\n"
        f"💰 Общий баланс: {user['stars_balance']}⭐\n"
        f"💎 Доступно для вывода (выигрыши): {winnable}⭐\n"
        f"💳 Внесено (не выводится): {deposited}⭐\n\n"
        f"• Минимальная сумма: 1000⭐\n"
        f"• Комиссия: 2%\n"
        f"• Вывод только выигранных звезд\n\n"
        f"👇 Нажми кнопку ниже чтобы начать вывод"
    )

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💸 Создать заявку на вывод", callback_data="withdraw_start")],
        [InlineKeyboardButton(text="📋 История выводов", callback_data="withdraw_history")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="profile")]
    ])

    await callback.message.edit_text(text, parse_mode='HTML', reply_markup=keyboard)
    await callback.answer()


@dp.callback_query(F.data == "withdraw_start")
async def withdraw_start(callback: CallbackQuery, state: FSMContext):
    """Начать процесс вывода"""
    winnable = db.get_winnable_balance(callback.from_user.id)

    if winnable < 1000:
        await callback.message.edit_text(
            f"❌ <b>Недостаточно выигранных звезд для вывода</b>\n\n"
            f"Доступно для вывода: {winnable}⭐\n"
            f"Минимальная сумма: 1000⭐\n\n"
            f"Играй и выигрывай больше!",
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="◀️ Назад", callback_data="withdraw_menu")]
            ])
        )
        await callback.answer()
        return

    text = (
        f"📤 <b>Создание заявки на вывод</b>\n\n"
        f"Доступно для вывода: {winnable}⭐\n"
        f"Минимальная сумма: 1000⭐\n"
        f"Комиссия: 2%\n\n"
        f"Введите сумму для вывода (только число):"
    )

    await state.set_state(WithdrawStates.waiting_for_amount)
    await callback.message.edit_text(text, parse_mode='HTML')
    await callback.answer()


@dp.message(WithdrawStates.waiting_for_amount)
async def process_withdraw_amount(message: Message, state: FSMContext):
    """Обработка ввода суммы вывода"""
    try:
        amount = int(message.text)
    except ValueError:
        await message.answer("❌ Пожалуйста, введите целое число")
        return

    if amount <= 0:
        await message.answer("❌ Сумма должна быть больше 0")
        return

    # Создаем заявку
    result = db.create_withdrawal_request(message.from_user.id, amount)

    if result['success']:
        # Уведомление админу
        user = db.get_user(message.from_user.id)
        try:
            await bot.send_message(
                chat_id=config.ADMIN_ID,
                text=(
                    f"🚨 <b>НОВАЯ ЗАЯВКА #{result['request_id']}</b>\n\n"
                    f"👤 Пользователь: @{user['username'] or 'нет'}\n"
                    f"🆔 ID: {message.from_user.id}\n"
                    f"⭐ Сумма: {amount}\n"
                    f"💎 Выиграно всего: {db.get_winnable_balance(message.from_user.id) + amount}⭐\n\n"
                    f"<i>Для подтверждения:</i> /approve {result['request_id']}\n"
                    f"<i>Для отклонения:</i> /reject {result['request_id']}"
                ),
                parse_mode='HTML'
            )
        except:
            pass

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Назад в профиль", callback_data="profile")]
        ])

        await message.answer(result['message'], parse_mode='HTML', reply_markup=keyboard)
    else:
        await message.answer(f"❌ {result['error']}")

    await state.clear()


@dp.callback_query(F.data == "withdraw_history")
async def withdraw_history(callback: CallbackQuery):
    """История выводов пользователя"""
    user = db.get_user(callback.from_user.id)

    conn = sqlite3.connect('stars_arena.db')
    cursor = conn.cursor()

    cursor.execute('''
        SELECT id, amount, status, created_at FROM withdrawal_requests_stars 
        WHERE user_id = ? 
        ORDER BY created_at DESC 
        LIMIT 10
    ''', (user['id'],))

    withdrawals = cursor.fetchall()
    conn.close()

    if not withdrawals:
        text = "📋 У вас пока нет заявок на вывод"
    else:
        text = "📋 <b>Последние заявки на вывод:</b>\n\n"
        for w in withdrawals:
            status_emoji = {
                'pending': '⏳',
                'approved': '✅',
                'rejected': '❌'
            }.get(w[2], '📝')
            text += f"{status_emoji} #{w[0]}: {w[1]}⭐ - {w[2]} ({w[3][:10]})\n"

    await callback.message.edit_text(
        text,
        parse_mode='HTML',
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Назад", callback_data="withdraw_menu")]
        ])
    )
    await callback.answer()


# ===== ПАРТНЕРСКАЯ ПРОГРАММА =====
@dp.callback_query(F.data == "partner")
async def partner_program(callback: CallbackQuery):
    """Партнерская программа"""
    user = db.get_user(callback.from_user.id)

    # Реферальная ссылка
    bot_info = await bot.get_me()
    ref_link = f"https://t.me/{bot_info.username}?start=ref_{user['telegram_id']}"

    # Статистика рефералов
    conn = sqlite3.connect('stars_arena.db')
    cursor = conn.cursor()

    cursor.execute('SELECT COUNT(*) FROM users WHERE referrer_id = ?', (user['id'],))
    referrals_count = cursor.fetchone()[0]

    cursor.execute('''
        SELECT COALESCE(SUM(b.amount), 0) FROM bets_stars b
        JOIN users u ON b.user_id = u.id
        WHERE u.referrer_id = ?
    ''', (user['id'],))
    referrals_bets = cursor.fetchone()[0]

    conn.close()

    # Доход 10% от ставок рефералов
    partner_income = int(referrals_bets * 0.1)

    text = (
        f"👥 <b>Партнерская программа</b>\n\n"
        f"🔗 Твоя реферальная ссылка:\n"
        f"<code>{ref_link}</code>\n\n"
        f"📊 Статистика:\n"
        f"• Приглашено друзей: {referrals_count}\n"
        f"• Сумма их ставок: {referrals_bets}⭐\n"
        f"• Твой доход (10%): {partner_income}⭐\n\n"
        f"Как это работает:\n"
        f"1. Отправь ссылку друзьям\n"
        f"2. Они играют и делают ставки\n"
        f"3. Ты получаешь 10% от каждой их ставки"
    )

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📋 Копировать ссылку", callback_data="copy_ref")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="profile")]
    ])

    await callback.message.edit_text(text, parse_mode='HTML', reply_markup=keyboard)
    await callback.answer()


@dp.callback_query(F.data == "copy_ref")
async def copy_ref_link(callback: CallbackQuery):
    """Копирование реферальной ссылки"""
    bot_info = await bot.get_me()
    ref_link = f"https://t.me/{bot_info.username}?start=ref_{callback.from_user.id}"

    await callback.message.answer(
        f"🔗 Твоя реферальная ссылка:\n<code>{ref_link}</code>\n\n"
        f"Отправь её друзьям!",
        parse_mode='HTML'
    )
    await callback.answer()


# ===== АДМИН-КОМАНДЫ =====
@dp.message(Command("approve"))
async def approve_withdrawal(message: Message):
    """Подтверждение вывода (админ)"""
    if message.from_user.id not in config.ADMIN_IDS:
        return

    try:
        request_id = int(message.text.split()[1])

        conn = sqlite3.connect('stars_arena.db')
        cursor = conn.cursor()
        cursor.execute('''
            SELECT user_id, amount FROM withdrawal_requests_stars 
            WHERE id = ? AND status = 'pending'
        ''', (request_id,))
        request = cursor.fetchone()

        if not request:
            await message.answer("❌ Заявка не найдена или уже обработана")
            conn.close()
            return

        user_id, amount = request
        cursor.execute('SELECT telegram_id FROM users WHERE id = ?', (user_id,))
        user_telegram_id = cursor.fetchone()[0]
        conn.close()

        # Подтверждаем
        db.approve_withdrawal_stars(request_id)

        await message.answer(f"✅ Заявка #{request_id} на {amount}⭐ подтверждена")

        try:
            await bot.send_message(
                user_telegram_id,
                f"✅ <b>Заявка на вывод #{request_id} подтверждена!</b>\n\n"
                f"Сумма: {amount}⭐\n"
                f"Статус: средства отправлены\n\n"
                f"<i>Если звезды не пришли в течение 24 часов, обратитесь в поддержку.</i>",
                parse_mode='HTML'
            )
        except:
            pass

    except (IndexError, ValueError):
        await message.answer("❌ Используйте: /approve <номер заявки>")


@dp.message(Command("reject"))
async def reject_withdrawal(message: Message):
    """Отклонение вывода (админ)"""
    if message.from_user.id not in config.ADMIN_IDS:
        return

    try:
        request_id = int(message.text.split()[1])

        conn = sqlite3.connect('stars_arena.db')
        cursor = conn.cursor()
        cursor.execute('''
            SELECT user_id, amount FROM withdrawal_requests_stars 
            WHERE id = ? AND status = 'pending'
        ''', (request_id,))
        request = cursor.fetchone()

        if not request:
            await message.answer("❌ Заявка не найдена или уже обработана")
            conn.close()
            return

        user_id, amount = request
        cursor.execute('SELECT telegram_id FROM users WHERE id = ?', (user_id,))
        user_telegram_id = cursor.fetchone()[0]
        conn.close()

        # Отклоняем
        db.reject_withdrawal_stars(request_id)

        await message.answer(f"✅ Заявка #{request_id} на {amount}⭐ отклонена")

        try:
            await bot.send_message(
                user_telegram_id,
                f"❌ <b>Заявка на вывод #{request_id} отклонена</b>\n\n"
                f"Сумма {amount}⭐ возвращена на баланс.\n\n"
                f"<i>Причина: проверьте правильность введенных данных или свяжитесь с поддержкой.</i>",
                parse_mode='HTML'
            )
        except:
            pass

    except (IndexError, ValueError):
        await message.answer("❌ Используйте: /reject <номер заявки>")


# ===== ЗАПУСК =====
async def main():
    logger.info("🚀 Запуск бота Stars Arena...")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
