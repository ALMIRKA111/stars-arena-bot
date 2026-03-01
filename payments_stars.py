import json
import logging
from aiogram import Bot, Dispatcher, Router, F
from aiogram.types import Message, CallbackQuery, PreCheckoutQuery, LabeledPrice, InlineKeyboardMarkup, \
    InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from database import db
from config import config

logger = logging.getLogger(__name__)
router = Router()


# Состояния для ввода суммы
class DepositStates(StatesGroup):
    waiting_for_amount = State()


# ===== МЕНЮ ПОПОЛНЕНИЯ =====
@router.callback_query(F.data == "show_deposit")
async def show_deposit_menu(callback: CallbackQuery):
    """Показать меню пополнения"""
    await callback.message.edit_text(
        "💎 <b>Пополнение баланса</b>\n\n"
        "Введи любую сумму от 10⭐:\n"
        "• Комиссия: 0%\n"
        "• Средства зачисляются мгновенно\n\n"
        "Просто напиши число в чат:",
        parse_mode='HTML',
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Назад", callback_data="profile")]
        ])
    )

    # Устанавливаем состояние ожидания ввода суммы
    await DepositStates.waiting_for_amount.set()
    await callback.answer()


# ===== ОБРАБОТКА ВВОДА СУММЫ =====
@router.message(DepositStates.waiting_for_amount)
async def process_deposit_amount(message: Message, state: FSMContext, bot: Bot):
    """Обработка введенной пользователем суммы"""

    # Проверяем, что введено число
    try:
        amount = int(message.text)
    except ValueError:
        await message.answer(
            "❌ Пожалуйста, введи целое число (например: 50)"
        )
        return

    # Проверяем минимальную сумму
    if amount < 10:
        await message.answer(
            "❌ Минимальная сумма пополнения: 10⭐\n"
            "Пожалуйста, введи другую сумму:"
        )
        return

    # Создаем счет
    await create_stars_invoice(message, state, bot, amount)


# ===== СОЗДАНИЕ СЧЕТА =====
async def create_stars_invoice(message: Message, state: FSMContext, bot: Bot, amount: int):
    """Создание счета на оплату в звездах"""

    # Генерируем уникальный payload для этого платежа
    payload = json.dumps({
        "user_id": message.from_user.id,
        "amount": amount,
        "type": "deposit",
        "username": message.from_user.username
    })

    # Создаем счет в Telegram Stars
    await bot.send_invoice(
        chat_id=message.from_user.id,
        title="Пополнение баланса",
        description=f"Пополнение игрового счета на {amount} звезд",
        payload=payload,
        provider_token="",  # Пустая строка для Stars
        currency="XTR",  # Специальная валюта для Stars
        prices=[LabeledPrice(label="Пополнение", amount=amount)],
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=f"💳 Оплатить {amount} ⭐", pay=True)]
        ])
    )

    # Сбрасываем состояние
    await state.clear()


# ===== ПРЕДПРОВЕРОЧНЫЙ ЗАПРОС =====
@router.pre_checkout_query()
async def pre_checkout_handler(pre_checkout_query: PreCheckoutQuery, bot: Bot):
    """Подтверждение платежа перед списанием"""
    try:
        # Проверяем валидность платежа
        payload = json.loads(pre_checkout_query.invoice_payload)
        user_id = payload.get("user_id")
        amount = payload.get("amount")

        # Можно добавить дополнительные проверки
        # Например, не пытался ли пользователь оплатить дважды

        # Подтверждаем платеж
        await bot.answer_pre_checkout_query(
            pre_checkout_query.id,
            ok=True
        )
        logger.info(f"✅ Платеж подтвержден: user={user_id}, amount={amount}")

    except Exception as e:
        logger.error(f"❌ Ошибка подтверждения платежа: {e}")
        await bot.answer_pre_checkout_query(
            pre_checkout_query.id,
            ok=False,
            error_message="Ошибка обработки платежа. Попробуйте позже."
        )


# ===== УСПЕШНЫЙ ПЛАТЕЖ =====
@router.message(F.successful_payment)
async def successful_payment_handler(message: Message, bot: Bot):
    """Обработка успешного платежа"""
    payment = message.successful_payment
    payload = json.loads(payment.invoice_payload)

    user_id = payload.get("user_id")
    amount = payment.total_amount  # Сумма в звездах

    # Зачисляем звезды на баланс пользователя
    success = db.add_stars(user_id, amount, 'deposit')

    if success:
        await message.answer(
            f"✅ <b>Пополнение успешно!</b>\n\n"
            f"На твой счет зачислено: <b>{amount}⭐</b>\n"
            f"Комиссия: 0%\n\n"
            f"Текущий баланс: {db.get_user(user_id)['stars_balance']}⭐\n\n"
            f"Ты можешь вернуться в игру через /menu",
            parse_mode='HTML'
        )

        # Уведомляем админа о платеже
        user = db.get_user(user_id)
        admin_text = (
            f"💰 <b>Новый платеж!</b>\n\n"
            f"👤 Пользователь: @{user['username'] or 'нет'}\n"
            f"💎 Сумма: {amount}⭐\n"
            f"🆔 ID: {user_id}\n"
            f"📊 Новый баланс: {user['stars_balance']}⭐"
        )
        await bot.send_message(
            chat_id=config.ADMIN_ID,
            text=admin_text,
            parse_mode='HTML'
        )
    else:
        await message.answer(
            "❌ Ошибка при зачислении средств.\n"
            "Пожалуйста, обратитесь в поддержку и сохраните этот чек.\n"
            "Поддержка: @support_bot",
            parse_mode='HTML'
        )
        logger.error(f"Ошибка зачисления средств user={user_id}, amount={amount}")


# ===== ОТМЕНА ОПЕРАЦИИ =====
@router.message(Command("cancel"))
async def cancel_deposit(message: Message, state: FSMContext):
    """Отмена операции пополнения"""
    current_state = await state.get_state()
    if current_state is not None:
        await state.clear()
        await message.answer(
            "❌ Операция отменена",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🎰 Вернуться в меню", callback_data="back_to_main")]
            ])
        )