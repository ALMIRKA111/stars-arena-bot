import asyncio
import json
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import LabeledPrice, InlineKeyboardMarkup, InlineKeyboardButton
from aiohttp import web

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

API_TOKEN = '8601754069:AAEmsv40xs0M77p6Z3n0t25sJp3fpJ8a_4k'
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

app = web.Application()


# ===== Команда /start =====
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎮 Открыть Mini App", web_app=types.WebAppInfo(url="https://your-domain.com"))]
    ])
    await message.answer("Добро пожаловать! Нажми кнопку ниже:", reply_markup=kb)


# ===== API для создания инвойса =====
async def create_invoice_handler(request):
    try:
        data = await request.json()
        amount = int(data.get('amount', 100))
        logger.info(f"Запрос на создание инвойса: {amount} звезд")

        invoice_link = await bot.create_invoice_link(
            title="Пополнение Stars Arena",
            description=f"Пополнение игрового счета на {amount} звёзд",
            payload=f"deposit_{amount}",
            provider_token="",
            currency="XTR",
            prices=[LabeledPrice(label="Пополнение", amount=amount)]
        )

        logger.info(f"Инвойс создан: {invoice_link}")
        return web.json_response({'success': True, 'link': invoice_link})
    except Exception as e:
        logger.error(f"Ошибка создания инвойса: {e}")
        return web.json_response({'success': False, 'error': str(e)}, status=500)


# ===== Обработка платежей =====
@dp.pre_checkout_query()
async def pre_checkout(pre_checkout_query: types.PreCheckoutQuery):
    await pre_checkout_query.answer(ok=True)
    logger.info(f"Платеж подтвержден: {pre_checkout_query.invoice_payload}")


@dp.message(F.successful_payment)
async def successful_payment(message: types.Message):
    payment = message.successful_payment
    amount = payment.total_amount
    await message.answer(
        f"✅ <b>Оплата прошла успешно!</b>\n\n"
        f"На ваш счет зачислено: <b>{amount} звезд</b>.",
        parse_mode='HTML'
    )


# ===== Запуск =====
async def main():
    # Настраиваем маршруты
    app.router.add_post('/api/create-invoice', create_invoice_handler)

    # Запускаем веб-сервер
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 8080)
    await site.start()

    logger.info("🚀 Веб-сервер запущен на порту 8080")
    logger.info("🤖 Бот запущен...")

    # Запускаем бота
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())