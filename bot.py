import asyncio
import json
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import LabeledPrice, InlineKeyboardMarkup, InlineKeyboardButton
from aiohttp import web
import socket

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Токен бота
API_TOKEN = '8601754069:AAEmsv40xs0M77p6Z3n0t25sJp3fpJ8a_4k'
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Веб-сервер для Mini App
app = web.Application()


# ===== КОМАНДЫ БОТА =====
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    """Стартовая команда"""
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎮 Открыть Mini App", web_app=types.WebAppInfo(url="https://your-domain.com"))]
    ])
    await message.answer("Добро пожаловать! Нажми кнопку ниже:", reply_markup=kb)


# ===== API ДЛЯ MINI APP =====
async def create_invoice_handler(request):
    """Создает ссылку на оплату по запросу из Mini App"""
    try:
        data = await request.json()
        amount = int(data.get('amount', 100))

        logger.info(f"Запрос на создание инвойса: {amount}⭐")

        # Создаем ссылку на оплату
        invoice_link = await bot.create_invoice_link(
            title="Пополнение Stars Arena",
            description=f"Пополнение игрового счета на {amount} звезд",
            payload=f"deposit_{amount}",
            provider_token="",
            currency="XTR",
            prices=[LabeledPrice(label="Пополнение", amount=amount)]
        )

        logger.info(f"Инвойс создан: {invoice_link}")

        return web.json_response({
            'success': True,
            'link': invoice_link
        })

    except Exception as e:
        logger.error(f"Ошибка создания инвойса: {e}")
        return web.json_response({
            'success': False,
            'error': str(e)
        }, status=500)


# ===== ОБРАБОТЧИКИ ПЛАТЕЖЕЙ =====
@dp.pre_checkout_query()
async def pre_checkout_handler(pre_checkout_query: types.PreCheckoutQuery):
    """Обязательно подтверждаем платеж"""
    await pre_checkout_query.answer(ok=True)
    logger.info(f"Платеж подтвержден: {pre_checkout_query.invoice_payload}")


@dp.message(F.successful_payment)
async def successful_payment_handler(message: types.Message):
    """Обработка успешной оплаты"""
    payment = message.successful_payment
    amount = payment.total_amount

    # Здесь можно добавить зачисление в БД
    await message.answer(
        f"✅ <b>Оплата прошла успешно!</b>\n\n"
        f"На ваш счет зачислено: <b>{amount}⭐</b>",
        parse_mode='HTML'
    )

    logger.info(f"Успешная оплата: {amount}⭐ от {message.from_user.id}")


# ===== ЗАПУСК =====
async def run_bot():
    """Запуск бота"""
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


async def run_server():
    """Запуск веб-сервера"""
    app.router.add_post('/api/create-invoice', create_invoice_handler)

    # Получаем локальный IP
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)

    logger.info(f"🌐 Сервер запущен на http://{local_ip}:8080")
    logger.info(f"📱 API доступен по адресу: http://{local_ip}:8080/api/create-invoice")

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 8080)
    await site.start()


async def main():
    """Главная функция"""
    logger.info("🚀 Запуск бота и веб-сервера...")

    # Запускаем оба сервиса одновременно
    await asyncio.gather(
        run_bot(),
        run_server()
    )


if __name__ == "__main__":
    asyncio.run(main())