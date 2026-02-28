import sqlite3
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

    # ===== ПОЛЬЗОВАТЕЛИ =====

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

        # Создаем запись о ставке
        cursor.execute('''
            INSERT INTO bets_stars (user_id, amount, color, win_percent)
            VALUES (?, ?, ?, ?)
        ''', (user_id, amount, color, win_percent))

        bet_id = cursor.lastrowid

        conn.commit()
        conn.close()

        return {'success': True, 'bet_id': bet_id}

    def place_bet_ton(self, telegram_id, amount, color, win_percent):
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT id, ton_balance FROM users WHERE telegram_id = ?', (telegram_id,))
        user = cursor.fetchone()

        if not user or user[1] < amount:
            conn.close()
            return {'success': False, 'error': 'Недостаточно TON'}

        user_id = user[0]

        # Списываем ставку
        cursor.execute('UPDATE users SET ton_balance = ton_balance - ? WHERE id = ?', (amount, user_id))

        # Создаем запись о ставке
        cursor.execute('''
            INSERT INTO bets_ton (user_id, amount, color, win_percent)
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

    def create_withdrawal_ton(self, telegram_id, amount, wallet):
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT id, ton_balance FROM users WHERE telegram_id = ?', (telegram_id,))
        user = cursor.fetchone()

        if not user or user[1] < amount:
            conn.close()
            return {'success': False, 'error': 'Недостаточно TON'}

        user_id = user[0]

        # Списываем TON
        cursor.execute('UPDATE users SET ton_balance = ton_balance - ? WHERE id = ?', (amount, user_id))

        # Создаем заявку
        cursor.execute('''
            INSERT INTO withdrawal_requests_ton (user_id, amount, wallet_address)
            VALUES (?, ?, ?)
        ''', (user_id, amount, wallet))

        request_id = cursor.lastrowid

        conn.commit()
        conn.close()

        return {'success': True, 'request_id': request_id}

    # ===== ПРОМОКОДЫ =====

    def use_promo_code(self, telegram_id, code):
        conn = self.get_connection()
        cursor = conn.cursor()

        # Проверяем существование промокода
        cursor.execute('SELECT * FROM promo_codes WHERE code = ?', (code,))
        promo = cursor.fetchone()

        if not promo:
            conn.close()
            return {'success': False, 'error': 'Промокод не найден'}

        promo_id = promo[0]
        stars_bonus = promo[2]
        ton_bonus = promo[3]
        max_uses = promo[4]
        used_count = promo[5]

        # Проверяем лимит использований
        if used_count >= max_uses:
            conn.close()
            return {'success': False, 'error': 'Промокод уже использован'}

        # Проверяем, не использовал ли пользователь этот промокод
        cursor.execute(
            'SELECT * FROM used_promos WHERE user_id = (SELECT id FROM users WHERE telegram_id = ?) AND promo_id = ?',
            (telegram_id, promo_id))
        if cursor.fetchone():
            conn.close()
            return {'success': False, 'error': 'Вы уже использовали этот промокод'}

        # Начисляем бонусы
        cursor.execute(
            'UPDATE users SET stars_balance = stars_balance + ?, ton_balance = ton_balance + ? WHERE telegram_id = ?',
            (stars_bonus, ton_bonus, telegram_id))

        # Увеличиваем счетчик использований
        cursor.execute('UPDATE promo_codes SET used_count = used_count + 1 WHERE id = ?', (promo_id,))

        # Записываем использование
        cursor.execute('''
            INSERT INTO used_promos (user_id, promo_id)
            VALUES ((SELECT id FROM users WHERE telegram_id = ?), ?)
        ''', (telegram_id, promo_id))

        conn.commit()
        conn.close()

        return {'success': True, 'stars_bonus': stars_bonus, 'ton_bonus': ton_bonus}


# Создаем глобальный объект
db = Database()