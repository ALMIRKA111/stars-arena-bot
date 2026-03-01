from flask import Flask, send_from_directory
import os
import sys
import multiprocessing

app = Flask(__name__, static_folder='mini_app')


@app.route('/')
def serve_mini_app():
    return send_from_directory('mini_app', 'index.html')


@app.route('/<path:path>')
def serve_static_files(path):
    return send_from_directory('mini_app', path)


def run_bot():
    """Запускает бота в отдельном ПРОЦЕССЕ (не потоке)"""
    import subprocess
    subprocess.run([sys.executable, "bot.py"])


if __name__ == "__main__":
    # Запускаем бота в отдельном процессе
    bot_process = multiprocessing.Process(target=run_bot)
    bot_process.start()

    # Запускаем Flask
    port = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=port)