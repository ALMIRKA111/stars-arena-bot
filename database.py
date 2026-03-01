import sqlite3
import random
from datetime import datetime, date, timedelta
from config import config


class Database:
    def __init__(self):
        self.db_path = 'stars_arena.db'
        self.init_db()

    def get_connection(self):
        return sqlite3.connect(self.db_path)

    def init_db(self):
        conn = self.get_connection()
        cursor = conn.cursor()

        # Таблица пользователей
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER UNIQUE NOT NULL,
                username TEXT,
                first_name TEXT,
                stars_balance INTEGER DEFAULT 0,
                ton_balance REAL DEFAULT 0,
                total_deposited_stars INTEGER DEFAULT 0,
                total_deposited_ton REAL DEFAULT 0,
                total_withdrawn_stars INTEGER DEFAULT 0,
                total_withdrawn_ton REAL DEFAULT 0,
                games_played INTEGER DEFAULT 0,
                games_won INTEGER DEFAULT 0,
                referrer_id INTEGER,
                promo_code TEXT UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (referrer_id) REFERENCES users (id)
            )
        ''')

        # Таблица ставок на звезды
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS bets_stars (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                amount INTEGER NOT NULL,
                color TEXT NOT NULL,
                win_percent INTEGER NOT NULL,
                result TEXT,
                profit INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')

        # Таблица ставок на TON
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS bets_ton (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                amount REAL NOT NULL,
                color TEXT NOT NULL,
                win_percent INTEGER NOT NULL,
                result TEXT,
                profit REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')

        # Таблица заявок на вывод (звезды)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS withdrawal_requests_stars (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                amount INTEGER NOT NULL,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                processed_at TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')

        # Таблица заявок на вывод (TON)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS withdrawal_requests_ton (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                amount REAL NOT NULL,
                wallet_address TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                processed_at TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')

        # Таблица транзакций
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                amount INTEGER NOT NULL,
                transaction_type TEXT NOT NULL,
                status TEXT DEFAULT 'completed',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')

        # Таблица промокодов
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS promo_codes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT UNIQUE NOT NULL,
                stars_bonus INTEGER DEFAULT 0,
                ton_bonus REAL DEFAULT 0,
                max_uses INTEGER DEFAULT 1,
                used_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Таблица использованных промокодов
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS used_promos (
                user_id INTEGER NOT NULL,
                promo_id INTEGER NOT NULL,
                used_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (promo_id) REFERENCES promo_codes (id)
            )
        ''')

        conn.commit()
        conn.close()
        print("✅ База данных инициализирована")

    # ===== РАБОТА С ПОЛЬЗОВАТЕЛЯМИ =====

    def get_user(self, telegram_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE telegram_id = ?', (telegram_id,))
        user = cursor.fetchone()
        conn.close()

        if user:
            return {
                'id': user[0],
                'telegram_id': user[1],
                'username': user[2],
                'first_name': user[3],
                'stars_balance': user[4],
                'ton_balance': user[5],
                'total_deposited_stars': user[6],
                'total_deposited_ton': user[7],
                'total_withdrawn_stars': user[8],
                'total_withdrawn_ton': user[9],
                'games_played': user[10],
                'games_won': user[11],
                'referrer_id': user[12],
                'promo_code': user[13],
                'created_at': user[14]
            }
        return None

    def create_user(self, telegram_id, username=None, first_name=None, referrer_id=None):
        conn = self.get_connection()
        cursor = conn.cursor()

        # Генерируем уникальный промокод
        promo_code = f"REF{telegram_id}"

        cursor.execute('''
            INSERT INTO users (telegram_id, username, first_name, promo_code, referrer_id)
            VALUES (?, ?, ?, ?, ?)
        ''', (telegram_id, username, first_name, promo_code, referrer_id))

        conn.commit()
        conn.close()
        return self.get_user(telegram_id)

    # ===== РАБОТА СО ЗВЕЗДАМИ =====

    def add_stars(self, telegram_id, amount, transaction_type='deposit'):
        """Добавить звезды пользователю"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Получаем пользователя
        cursor.execute('SELECT id, stars_balance FROM users WHERE telegram_id = ?', (telegram_id,))
        user = cursor.fetchone()

        if not user:
            conn.close()
            return False

        user_id = user[0]
        current_balance = user[1]

        # Обновляем баланс
        cursor.execute('UPDATE users SET stars_balance = stars_balance + ? WHERE id = ?', (amount, user_id))

        # Обновляем общую сумму пополнений
        if transaction_type == 'deposit':
            cursor.execute('UPDATE users SET total_deposited_stars = total_deposited_stars + ? WHERE id = ?',
                           (amount, user_id))

        # Записываем транзакцию
        cursor.execute('''
            INSERT INTO transactions (user_id, amount, transaction_type)
            VALUES (?, ?, ?)
        ''', (user_id, amount, transaction_type))

        conn.commit()
        conn.close()
        return True

    def get_winnable_balance(self, telegram_id):
        """
        Возвращает баланс, который можно вывести (выигранные звезды)
        Выигранными считаются звезды, полученные от других пользователей
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT id FROM users WHERE telegram_id = ?', (telegram_id,))
        user = cursor.fetchone()

        if not user:
            conn.close()
            return 0

        user_id = user[0]

        # Считаем сколько всего было выиграно
        cursor.execute('''
            SELECT COALESCE(SUM(profit), 0) FROM bets_stars 
            WHERE user_id = ? AND result = 'win'
        ''', (user_id,))
        total_won = cursor.fetchone()[0] or 0

        # Считаем сколько уже было выведено выигрышей
        cursor.execute('''
            SELECT COALESCE(SUM(amount), 0) FROM withdrawal_requests_stars 
            WHERE user_id = ? AND status = 'approved'
        ''', (user_id,))
        total_withdrawn_wins = cursor.fetchone()[0] or 0

        conn.close()

        # Выигранные минус уже выведенные
        return max(0, total_won - total_withdrawn_wins)

    def get_deposit_balance(self, telegram_id):
        """
        Возвращает баланс внесенных звезд (невыводимые)
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT id, stars_balance, total_deposited_stars FROM users WHERE telegram_id = ?',
                       (telegram_id,))
        user = cursor.fetchone()

        if not user:
            conn.close()
            return 0

        user_id = user[0]
        total_balance = user[1]
        total_deposited = user[2]

        # Внесенные звезды = сколько всего внес
        deposited = total_deposited

        # Сколько из внесенных уже потрачено на ставки
        cursor.execute('''
            SELECT COALESCE(SUM(amount), 0) FROM bets_stars 
            WHERE user_id = ?
        ''', (user_id,))
        total_bet = cursor.fetchone()[0] or 0

        conn.close()

        # Остаток внесенных = внес - потрачено (но не меньше 0)
        return max(0, deposited - total_bet)

    def create_withdrawal_request(self, telegram_id, amount):
        """
        Обновленная функция создания заявки на вывод
        """
        # Проверка минимальной суммы (реальная для Fragment)
        if amount < 1000:
            return {
                'success': False,
                'error': f'Минимальная сумма вывода: 1000⭐\nУ вас запрошено: {amount}⭐'
            }

        # Проверяем, что сумма не больше баланса
        user = self.get_user(telegram_id)
        if not user or user['stars_balance'] < amount:
            return {'success': False, 'error': 'Недостаточно звезд'}

        # Проверяем, что выводим только выигранные звезды
        winnable = self.get_winnable_balance(telegram_id)
        if amount > winnable:
            return {
                'success': False,
                'error': f'Можно выводить только выигранные звезды.\nДоступно для вывода: {winnable}⭐'
            }

        # Создаем заявку
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT id FROM users WHERE telegram_id = ?', (telegram_id,))
        user_id = cursor.fetchone()[0]

        # Списываем звезды
        cursor.execute('UPDATE users SET stars_balance = stars_balance - ? WHERE id = ?', (amount, user_id))

        # Создаем заявку
        cursor.execute('''
            INSERT INTO withdrawal_requests_stars (user_id, amount)
            VALUES (?, ?)
        ''', (user_id, amount))

        request_id = cursor.lastrowid

        conn.commit()
        conn.close()

        return {
            'success': True,
            'request_id': request_id,
            'message': f'✅ Заявка на вывод {amount}⭐ создана!\n'
                       f'Статус: ожидает подтверждения админа\n'
                       f'Комиссия: 2% (будет удержана при выплате)'
        }


    def spend_stars(self, telegram_id, amount):
        """Потратить звезды (для ставок)"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT stars_balance FROM users WHERE telegram_id = ?', (telegram_id,))
        result = cursor.fetchone()

        if not result or result[0] < amount:
            conn.close()
            return False

        cursor.execute('''
            UPDATE users SET stars_balance = stars_balance - ? WHERE telegram_id = ?
        ''', (amount, telegram_id))

        conn.commit()
        conn.close()
        return True

    # ===== СТАВКИ =====

    def place_bet_stars(self, telegram_id, amount, color, win_percent):
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT id, stars_balance FROM users WHERE telegram_id = ?', (telegram_id,))
        user = cursor.fetchone()

        if not user or user[1] < amount:
            conn.close()
            return {'success': False, 'error': 'Недостаточно звезд'}

        user_id = user[0]

        # Списываем ставку
        cursor.execute('UPDATE users SET stars_balance = stars_balance - ? WHERE id = ?', (amount, user_id))

        # Обновляем статистику
        cursor.execute('UPDATE users SET games_played = games_played + 1 WHERE id = ?', (user_id,))

        # Создаем запись о ставке
        cursor.execute('''
            INSERT INTO bets_stars (user_id, amount, color, win_percent)
            VALUES (?, ?, ?, ?)
        ''', (user_id, amount, color, win_percent))

        bet_id = cursor.lastrowid

        conn.commit()
        conn.close()

        return {'success': True, 'bet_id': bet_id}

    def process_win_stars(self, bet_id, profit):
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT user_id, amount FROM bets_stars WHERE id = ?', (bet_id,))
        bet = cursor.fetchone()

        if bet:
            user_id = bet[0]
            bet_amount = bet[1]

            # Начисляем выигрыш (ставка возвращается + прибыль)
            cursor.execute('UPDATE users SET stars_balance = stars_balance + ?, games_won = games_won + 1 WHERE id = ?',
                           (bet_amount + profit, user_id))

            cursor.execute('UPDATE bets_stars SET result = "win", profit = ? WHERE id = ?', (profit, bet_id))

        conn.commit()
        conn.close()

    def process_lose_stars(self, bet_id):
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('UPDATE bets_stars SET result = "lose" WHERE id = ?', (bet_id,))

        conn.commit()
        conn.close()

    # ===== ВЫВОД =====

    def create_withdrawal_stars(self, telegram_id, amount):
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT id, stars_balance FROM users WHERE telegram_id = ?', (telegram_id,))
        user = cursor.fetchone()

        if not user or user[1] < amount:
            conn.close()
            return {'success': False, 'error': 'Недостаточно звезд'}

        user_id = user[0]

        # Списываем звезды
        cursor.execute('UPDATE users SET stars_balance = stars_balance - ? WHERE id = ?', (amount, user_id))

        # Создаем заявку
        cursor.execute('''
            INSERT INTO withdrawal_requests_stars (user_id, amount)
            VALUES (?, ?)
        ''', (user_id, amount))

        request_id = cursor.lastrowid

        conn.commit()
        conn.close()

        return {'success': True, 'request_id': request_id}

    def approve_withdrawal_stars(self, request_id):
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            UPDATE withdrawal_requests_stars 
            SET status = 'approved', processed_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (request_id,))

        conn.commit()
        conn.close()
        return {'success': True}

    def reject_withdrawal_stars(self, request_id):
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            UPDATE withdrawal_requests_stars 
            SET status = 'rejected', processed_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (request_id,))

        conn.commit()
        conn.close()
        return {'success': True}

    # ===== ТРАНЗАКЦИИ =====

    def get_user_transactions(self, telegram_id, limit=10):
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT id FROM users WHERE telegram_id = ?', (telegram_id,))
        user = cursor.fetchone()

        if not user:
            conn.close()
            return []

        user_id = user[0]

        cursor.execute('''
            SELECT * FROM transactions 
            WHERE user_id = ? 
            ORDER BY created_at DESC 
            LIMIT ?
        ''', (user_id, limit))

        transactions = cursor.fetchall()
        conn.close()

        result = []
        for t in transactions:
            result.append({
                'id': t[0],
                'user_id': t[1],
                'amount': t[2],
                'type': t[3],
                'status': t[4],
                'created_at': t[5]
            })

        return result


# Создаем глобальный объект
db = Database()