import random
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from database import db
from config import config

router = Router()


# Состояния для рулетки
class RouletteStates(StatesGroup):
    waiting_for_bet_stars = State()
    waiting_for_bet_ton = State()


# ===== РУЛЕТКА =====
class Roulette:
    def __init__(self, currency):
        self.currency = currency  # 'stars' или 'ton'
        self.colors = ['🔴 Красный', '⚫️ Черный', '🟢 Зеленый']
        self.bets = []  # [(user_id, amount, color, percent)]
        self.user_states = {}  # {user_id: {'amount': x, 'color': y, 'percent': z}}

    def generate_random_bet(self):
        """Генерирует случайный цвет и процент"""
        color = random.choice(self.colors)
        percent = random.randint(1, 100)
        return color, percent

    def add_bet(self, user_id, amount, color, percent):
        """Добавить ставку"""
        self.bets.append((user_id, amount, color, percent))

    def get_total_pool(self):
        """Общий банк"""
        if self.currency == 'stars':
            return sum(bet[1] for bet in self.bets)
        else:
            return round(sum(bet[1] for bet in self.bets), 2)

    def get_color_stats(self):
        """Статистика по цветам"""
        stats = {color: 0 for color in self.colors}

        for _, amount, color, _ in self.bets:
            stats[color] += amount

        total = self.get_total_pool()

        result = {}
        for color, amount in stats.items():
            if total > 0:
                percent = (amount / total) * 100
            else:
                percent = 0
            result[color] = {
                'amount': amount,
                'percent': round(percent, 2)
            }

        return result

    def spin(self):
        """Крутить рулетку - определяем победителя"""
        if not self.bets:
            return None

        # Выбираем победителя по проценту
        # Чем больше процент игрока, тем выше шанс
        total_percent = sum(bet[3] for bet in self.bets)
        r = random.uniform(0, total_percent)

        cumulative = 0
        winner_bet = None
        for bet in self.bets:
            cumulative += bet[3]
            if r <= cumulative:
                winner_bet = bet
                break

        if not winner_bet:
            winner_bet = random.choice(self.bets)

        user_id, amount, color, percent = winner_bet
        total_pool = self.get_total_pool()

        # Выигрыш = его ставка + (общий банк - его ставка)
        # За вычетом комиссии
        if self.currency == 'stars':
            win_amount = amount + (total_pool - amount)
            commission = int(win_amount * config.GAME_COMMISSION / 100)
            final_win = win_amount - commission
        else:
            win_amount = amount + (total_pool - amount)
            commission = round(win_amount * config.GAME_COMMISSION / 100, 2)
            final_win = round(win_amount - commission, 2)

        return {
            'winner_user_id': user_id,
            'winner_color': color,
            'winner_percent': percent,
            'winner_amount': amount,
            'win_amount': final_win,
            'commission': commission,
            'total_pool': total_pool
        }

    def clear(self):
        """Очистить рулетку"""
        self.bets = []
        self.user_states = {}


# Создаем рулетки
roulette_stars = Roulette('stars')
roulette_ton = Roulette('ton')


# ===== ФУНКЦИИ ОТОБРАЖЕНИЯ =====
def get_roulette_text(currency):
    """Формирует текст рулетки с банком и статистикой"""
    roulette = roulette_stars if currency == 'stars' else roulette_ton

    total_pool = roulette.get_total_pool()
    stats = roulette.get_color_stats()

    # Формируем строку с процентами
    percents = []
    for color in roulette.colors:
        percent = stats.get(color, {}).get('percent', 0)
        percents.append(f"{percent}%")

    text = (
        f"🎰 <b>Рулетка {'⭐ Stars' if currency == 'stars' else '💎 TON'}</b>\n\n"
        f"<b>БАНК</b>\n"
        f"{'⭐' if currency == 'stars' else '💎'} {total_pool} {'stars' if currency == 'stars' else 'TON'}\n\n"
        f"<b>ВЫБИРАЕМ ПОБЕДИТЕЛЯ</b>\n"
        f"{percents[0]}    {percents[1]}    {percents[2]}\n\n"
    )

    return text


def get_user_bet_text(currency, amount, color, percent):
    """Текст текущей ставки пользователя"""
    currency_symbol = '⭐' if currency == 'stars' else '💎'

    return (
        f"<b>Твоя ставка:</b>\n"
        f"{currency_symbol} {amount}   Шанс: {percent}%   Цвет: {color}\n\n"
        f"👇 Нажми кнопку чтобы сделать ставку"
    )


def get_roulette_keyboard(currency, user_id):
    """Клавиатура для рулетки"""
    from aiogram.types import InlineKeyboardButton
    from aiogram.utils.keyboard import InlineKeyboardBuilder

    builder = InlineKeyboardBuilder()
    roulette = roulette_stars if currency == 'stars' else roulette_ton

    # Кнопки с суммами
    if currency == 'stars':
        amounts = [10, 50, 100, 500, 1000]
    else:
        amounts = [0.1, 0.5, 1, 5, 10]

    row = []
    for amount in amounts:
        row.append(InlineKeyboardButton(
            text=f"{amount}",
            callback_data=f"roulette_{currency}_amount_{amount}"
        ))
    builder.row(*row, width=5)

    # Если пользователь уже выбрал сумму, показываем его шанс
    if user_id in roulette.user_states:
        state = roulette.user_states[user_id]
        builder.row(InlineKeyboardButton(
            text=f"🎲 СДЕЛАТЬ СТАВКУ ({state['color']} {state['percent']}%)",
            callback_data=f"roulette_{currency}_place"
        ))

    builder.row(InlineKeyboardButton(
        text="◀️ Назад",
        callback_data="back_to_main"
    ))

    return builder.as_markup()


# ===== ОБРАБОТЧИКИ =====
@router.callback_query(F.data == "roulette_stars")
async def show_roulette_stars(callback: CallbackQuery):
    """Показать рулетку на звезды"""
    user_id = callback.from_user.id

    text = get_roulette_text('stars')
    text += "\n👇 Выбери сумму ставки:"

    await callback.message.edit_text(
        text,
        reply_markup=get_roulette_keyboard('stars', user_id),
        parse_mode='HTML'
    )
    await callback.answer()


@router.callback_query(F.data == "roulette_ton")
async def show_roulette_ton(callback: CallbackQuery):
    """Показать рулетку на TON"""
    user_id = callback.from_user.id

    text = get_roulette_text('ton')
    text += "\n👇 Выбери сумму ставки:"

    await callback.message.edit_text(
        text,
        reply_markup=get_roulette_keyboard('ton', user_id),
        parse_mode='HTML'
    )
    await callback.answer()


@router.callback_query(F.data.startswith("roulette_stars_amount_"))
async def select_stars_amount(callback: CallbackQuery):
    """Выбор суммы в рулетке stars"""
    user_id = callback.from_user.id
    amount = int(callback.data.split("_")[3])

    # Генерируем случайный цвет и процент
    color = random.choice(roulette_stars.colors)
    percent = random.randint(1, 100)

    # Сохраняем состояние
    roulette_stars.user_states[user_id] = {
        'amount': amount,
        'color': color,
        'percent': percent
    }

    text = get_roulette_text('stars')
    text += get_user_bet_text('stars', amount, color, percent)

    await callback.message.edit_text(
        text,
        reply_markup=get_roulette_keyboard('stars', user_id),
        parse_mode='HTML'
    )
    await callback.answer()


@router.callback_query(F.data.startswith("roulette_ton_amount_"))
async def select_ton_amount(callback: CallbackQuery):
    """Выбор суммы в рулетке ton"""
    user_id = callback.from_user.id
    amount = float(callback.data.split("_")[3])

    # Генерируем случайный цвет и процент
    color = random.choice(roulette_ton.colors)
    percent = random.randint(1, 100)

    # Сохраняем состояние
    roulette_ton.user_states[user_id] = {
        'amount': amount,
        'color': color,
        'percent': percent
    }

    text = get_roulette_text('ton')
    text += get_user_bet_text('ton', amount, color, percent)

    await callback.message.edit_text(
        text,
        reply_markup=get_roulette_keyboard('ton', user_id),
        parse_mode='HTML'
    )
    await callback.answer()


@router.callback_query(F.data == "roulette_stars_place")
async def place_stars_bet(callback: CallbackQuery):
    """Разместить ставку в рулетке stars"""
    user_id = callback.from_user.id

    if user_id not in roulette_stars.user_states:
        await callback.answer("❌ Сначала выбери сумму!")
        return

    state = roulette_stars.user_states[user_id]
    amount = state['amount']
    color = state['color']
    percent = state['percent']

    # Проверяем баланс
    user = db.get_user(user_id)
    if not user or user['stars_balance'] < amount:
        await callback.answer("❌ Недостаточно звезд!")
        return

    # Размещаем ставку
    result = db.place_bet_stars(user_id, amount, color, percent)

    if result['success']:
        # Добавляем в рулетку
        roulette_stars.add_bet(user_id, amount, color, percent)

        # Удаляем состояние
        del roulette_stars.user_states[user_id]

        await callback.answer("✅ Ставка принята!")

        # Показываем обновленную рулетку
        text = get_roulette_text('stars')
        text += f"\n✅ Твоя ставка {amount}⭐ на {color} с шансом {percent}% принята!"

        await callback.message.edit_text(
            text,
            reply_markup=get_roulette_keyboard('stars', user_id),
            parse_mode='HTML'
        )
    else:
        await callback.answer("❌ Ошибка при ставке")


@router.callback_query(F.data == "roulette_ton_place")
async def place_ton_bet(callback: CallbackQuery):
    """Разместить ставку в рулетке ton"""
    user_id = callback.from_user.id

    if user_id not in roulette_ton.user_states:
        await callback.answer("❌ Сначала выбери сумму!")
        return

    state = roulette_ton.user_states[user_id]
    amount = state['amount']
    color = state['color']
    percent = state['percent']

    # Проверяем баланс
    user = db.get_user(user_id)
    if not user or user['ton_balance'] < amount:
        await callback.answer("❌ Недостаточно TON!")
        return

    # Размещаем ставку
    result = db.place_bet_ton(user_id, amount, color, percent)

    if result['success']:
        # Добавляем в рулетку
        roulette_ton.add_bet(user_id, amount, color, percent)

        # Удаляем состояние
        del roulette_ton.user_states[user_id]

        await callback.answer("✅ Ставка принята!")

        # Показываем обновленную рулетку
        text = get_roulette_text('ton')
        text += f"\n✅ Твоя ставка {amount}TON на {color} с шансом {percent}% принята!"

        await callback.message.edit_text(
            text,
            reply_markup=get_roulette_keyboard('ton', user_id),
            parse_mode='HTML'
        )
    else:
        await callback.answer("❌ Ошибка при ставке")