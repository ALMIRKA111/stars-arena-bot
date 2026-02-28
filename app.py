from flask import Flask, send_from_directory
import os
import subprocess
import sys

# Создаем веб-приложение
app = Flask(__name__, static_folder='mini_app')


# Отдаем Mini App
@app.route('/')
def serve_mini_app():
    return send_from_directory('mini_app', 'index.html')


# Отдаем стили и скрипты
@app.route('/<path:path>')
def serve_static_files(path):
    return send_from_directory('mini_app', path)


# Эта функция запустится при старте
def run_bot():
    from bot import main
    import asyncio
    asyncio.run(main())


if __name__ == "__main__":
    # Запускаем бота в фоне
    import threading

    bot_thread = threading.Thread(target=run_bot)
    bot_thread.start()

    # Запускаем веб-сервер
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port)