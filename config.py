import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # Токен бота
    BOT_TOKEN = os.getenv('BOT_TOKEN')
    ADMIN_ID = int(os.getenv('ADMIN_ID', 0))

    # Название бота
    BOT_NAME = "✨ Stars Arena"
    BOT_DESCRIPTION = "Рулетка на Telegram Stars и TON"

    # Комиссии
    GAME_COMMISSION = 5  # 5% при выигрыше
    WITHDRAW_COMMISSION = 2  # 2% при выводе
    DEPOSIT_COMMISSION = 0  # 0% при пополнении

    # Админ для уведомлений
    ADMIN_USERNAME = "@Former_Lord"

    # Минимальные ставки
    MIN_BET_STARS = 10  # минимум 10 звезд
    MIN_BET_TON = 0.1  # минимум 0.1 TON

config = Config()
