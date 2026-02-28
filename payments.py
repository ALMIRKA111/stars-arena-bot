from database import db
from config import config
from datetime import datetime


class Payments:
    """Класс для работы с платежами"""

    async def withdraw_stars(self, telegram_id, amount, bot=None):
        """Заявка на вывод Stars"""
        user = db.get_user(telegram_id)

        if not user:
            return {'success': False, 'error': 'Пользователь не найден'}

        if user['stars_balance'] < amount:
            return {'success': False, 'error': 'Недостаточно звезд'}

        # Комиссия 2%
        commission = int(amount * config.WITHDRAW_COMMISSION / 100)
        final_amount = amount - commission

        # Создаем заявку
        result = db.create_withdrawal_stars(telegram_id, final_amount)

        if result['success']:
            # Уведомление админу
            await self._notify_admin(
                bot,
                result['request_id'],
                telegram_id,
                final_amount,
                'stars'
            )

            return {
                'success': True,
                'request_id': result['request_id'],
                'amount': final_amount,
                'commission': commission,
                'message': f'✅ Заявка на вывод {final_amount}⭐ создана!\nКомиссия: {commission}⭐'
            }
        return result

    async def withdraw_ton(self, telegram_id, amount, wallet, bot=None):
        """Заявка на вывод TON"""
        user = db.get_user(telegram_id)

        if not user:
            return {'success': False, 'error': 'Пользователь не найден'}

        if user['ton_balance'] < amount:
            return {'success': False, 'error': 'Недостаточно TON'}

        # Комиссия 2%
        commission = round(amount * config.WITHDRAW_COMMISSION / 100, 2)
        final_amount = round(amount - commission, 2)

        # Создаем заявку
        result = db.create_withdrawal_ton(telegram_id, final_amount, wallet)

        if result['success']:
            # Уведомление админу
            await self._notify_admin(
                bot,
                result['request_id'],
                telegram_id,
                final_amount,
                'ton',
                wallet
            )

            return {
                'success': True,
                'request_id': result['request_id'],
                'amount': final_amount,
                'commission': commission,
                'message': f'✅ Заявка на вывод {final_amount} TON создана!\nКомиссия: {commission} TON'
            }
        return result

    async def _notify_admin(self, bot, request_id, telegram_id, amount, currency, wallet=None):
        """Отправить уведомление админу"""
        user = db.get_user(telegram_id)

        if not user:
            return

        if currency == 'stars':
            text = (
                f"🚨 <b>НОВАЯ ЗАЯВКА #{request_id}</b>\n\n"
                f"👤 Пользователь: @{user['username'] or 'нет'}\n"
                f"🆔 ID: <code>{telegram_id}</code>\n"
                f"⭐ Сумма: {amount} Stars\n"
                f"📅 {datetime.now().strftime('%d.%m.%Y %H:%M')}\n\n"
                f"<i>/approve_stars {request_id}</i>"
            )
        else:
            text = (
                f"🚨 <b>НОВАЯ ЗАЯВКА #{request_id}</b>\n\n"
                f"👤 Пользователь: @{user['username'] or 'нет'}\n"
                f"🆔 ID: <code>{telegram_id}</code>\n"
                f"💎 Сумма: {amount} TON\n"
                f"💳 Кошелек: <code>{wallet}</code>\n"
                f"📅 {datetime.now().strftime('%d.%m.%Y %H:%M')}\n\n"
                f"<i>/approve_ton {request_id}</i>"
            )

        try:
            if bot:
                await bot.send_message(config.ADMIN_ID, text, parse_mode='HTML')
                print(f"✅ Уведомление админу отправлено для заявки #{request_id}")
        except Exception as e:
            print(f"❌ Ошибка отправки админу: {e}")


# СОЗДАЕМ ОБЪЕКТ В КОНЦЕ ФАЙЛА
payments = Payments()