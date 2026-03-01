// Инициализация Telegram WebApp
let tg = window.Telegram.WebApp;
tg.ready();
tg.expand();

// Данные пользователя
let currentUser = null;
let mockData = {
    balance: 0,
    bank: 0,
    players: [],
    partner: {
        totalEarned: 0,
        referrals: 0,
        activeReferrals: 0,
        availableToWithdraw: 0
    }
};

// 15 цветов для игры
const colors = [
    '🔴 Красный', '🔵 Синий', '🟢 Зеленый', '🟡 Желтый', '🟣 Фиолетовый',
    '🟠 Оранжевый', '⚫️ Черный', '⚪️ Белый', '🟤 Коричневый', '💗 Розовый',
    '🩵 Голубой', '💚 Лайм', '🧡 Мандарин', '🤎 Шоколад', '🩶 Серый'
];

// Получаем пользователя
if (tg.initDataUnsafe && tg.initDataUnsafe.user) {
    currentUser = tg.initDataUnsafe.user;
    document.getElementById('username').textContent = currentUser.first_name || 'Игрок';
} else {
    currentUser = { id: 123456789, first_name: 'Тест' };
    document.getElementById('username').textContent = 'Тестовый режим';
}

// Обновление интерфейса
function updateUI() {
    document.getElementById('balance').textContent = mockData.balance;
    document.getElementById('bank-value').textContent = mockData.bank;
    document.getElementById('profile-balance').textContent = mockData.balance;
    document.getElementById('profile-games').textContent = mockData.players.length;

    // Обновляем список игроков
    const playersList = document.getElementById('players-list');
    if (playersList) {
        if (mockData.players.length === 0) {
            playersList.innerHTML = '<div class="empty-players">Пока нет ставок</div>';
        } else {
            let html = '';
            mockData.players.forEach((player, index) => {
                html += `
                    <div class="player-item ${player.isYou ? 'you' : ''}">
                        <span class="player-number">#${index + 1}</span>
                        <span class="player-color">${player.color}</span>
                        <span class="player-percent">${player.percent.toFixed(2)}%</span>
                    </div>
                `;
            });
            playersList.innerHTML = html;
        }
    }
}

// ===== ВКЛАДКИ =====
const pvpTab = document.getElementById('pvp-tab');
const profileTab = document.getElementById('profile-tab');
const pvpBtn = document.getElementById('pvp-btn');
const profileBtn = document.getElementById('profile-btn');

if (pvpBtn && profileBtn) {
    pvpBtn.addEventListener('click', () => {
        pvpTab.style.display = 'block';
        profileTab.style.display = 'none';
        pvpBtn.classList.add('active');
        profileBtn.classList.remove('active');
    });

    profileBtn.addEventListener('click', () => {
        pvpTab.style.display = 'none';
        profileTab.style.display = 'block';
        profileBtn.classList.add('active');
        pvpBtn.classList.remove('active');
    });
}

// ===== ИГРОВАЯ ЛОГИКА =====
const betInput = document.getElementById('bet-amount-input');
const okBtn = document.getElementById('ok-btn');
const placeBetBtn = document.getElementById('place-bet');

let selectedAmount = null;
let myCurrentBet = null;

if (okBtn) {
    okBtn.addEventListener('click', () => {
        const amount = parseInt(betInput.value);

        if (!amount || amount <= 0) {
            tg.showAlert('❌ Введи сумму ставки');
            return;
        }

        if (amount > mockData.balance) {
            tg.showAlert('❌ Недостаточно средств');
            return;
        }

        selectedAmount = amount;
        const randomColor = colors[Math.floor(Math.random() * colors.length)];

        myCurrentBet = {
            amount: selectedAmount,
            color: randomColor,
            percent: 0
        };

        document.getElementById('bet-info').style.display = 'flex';
        document.getElementById('bet-amount-display').textContent = selectedAmount;
        document.getElementById('bet-percent-display').textContent = '0';
        document.getElementById('bet-color-display').textContent = randomColor;
        placeBetBtn.style.display = 'block';
        betInput.value = '';
    });
}

if (placeBetBtn) {
    placeBetBtn.addEventListener('click', () => {
        if (!myCurrentBet) return;

        const newPlayer = {
            color: myCurrentBet.color,
            amount: myCurrentBet.amount,
            percent: 0,
            isYou: true
        };
        mockData.players.push(newPlayer);

        mockData.bank += myCurrentBet.amount;
        mockData.balance -= myCurrentBet.amount;

        mockData.players.forEach(player => {
            player.percent = (player.amount / mockData.bank) * 100;
        });

        placeBetBtn.style.display = 'none';
        document.getElementById('bet-info').style.display = 'none';
        myCurrentBet = null;
        selectedAmount = null;

        updateUI();

        tg.showPopup({
            title: '✅ Ставка принята!',
            message: `Твоя ставка ${newPlayer.amount}⭐ на ${newPlayer.color}`,
            buttons: [{ type: 'ok' }]
        });
    });
}

// ===== ПОПОЛНЕНИЕ =====
const depositInput = document.getElementById('deposit-amount');
const depositBtn = document.getElementById('deposit-btn');

if (depositBtn) {
    depositBtn.addEventListener('click', () => {
        const amount = parseInt(depositInput.value);

        if (!amount || amount < 10) {
            tg.showAlert('❌ Минимальная сумма: 10⭐');
            return;
        }

        tg.sendData(JSON.stringify({
            action: 'deposit',
            amount: amount
        }));

        tg.showPopup({
            title: 'Запрос отправлен',
            message: `Ожидайте счёт от бота на ${amount}⭐`,
            buttons: [{ type: 'ok' }]
        });

        tg.close();
    });
}

// ===== ВЫВОД =====
const withdrawBtn = document.getElementById('withdraw-btn');
if (withdrawBtn) {
    withdrawBtn.addEventListener('click', () => {
        const amount = prompt('Введите сумму для вывода (мин. 1000⭐):');
        if (amount) {
            tg.showPopup({
                title: 'Заявка создана',
                message: `Заявка на вывод ${amount}⭐ отправлена администратору`,
                buttons: [{ type: 'ok' }]
            });
        }
    });
}

// ===== ПАРТНЕРСКАЯ ПРОГРАММА =====
const partnerBtn = document.getElementById('partner-btn');
if (partnerBtn) {
    partnerBtn.addEventListener('click', () => {
        const refLink = `https://t.me/${tg.initDataUnsafe.user?.username || 'bot'}?start=ref_${currentUser.id}`;
        tg.showPopup({
            title: 'Партнерская программа',
            message: `Твоя ссылка: ${refLink}\n\n10% от ставок друзей`,
            buttons: [{ type: 'ok' }]
        });
    });
}

// ===== ПОДДЕРЖКА =====
const supportBtn = document.getElementById('support-btn');
if (supportBtn) {
    supportBtn.addEventListener('click', () => {
        tg.showPopup({
            title: 'Поддержка',
            message: 'Свяжитесь с @support_bot',
            buttons: [{ type: 'ok' }]
        });
    });
}

// ===== ПРОМОКОД =====
const promoBtn = document.getElementById('promo-btn');
if (promoBtn) {
    promoBtn.addEventListener('click', () => {
        const promo = prompt('Введите промокод:');
        if (promo) {
            tg.showPopup({
                title: 'Промокод активирован',
                message: 'Получено 50⭐',
                buttons: [{ type: 'ok' }]
            });
            mockData.balance += 50;
            updateUI();
        }
    });
}

// Функция для пополнения (для onclick)
function showDeposit() {
    let amount = prompt('Введите сумму пополнения (от 10⭐):');
    if (amount) {
        amount = parseInt(amount);
        if (amount >= 10) {
            tg.sendData(JSON.stringify({
                action: 'deposit',
                amount: amount
            }));

            tg.showPopup({
                title: 'Запрос отправлен',
                message: `Ожидайте счёт на ${amount}⭐`,
                buttons: [{ type: 'ok' }]
            });

            tg.close();
        } else {
            tg.showAlert('❌ Минимальная сумма: 10⭐');
        }
    }
}

// Функция для вывода (для onclick)
function showWithdraw() {
    tg.showAlert('Вывод временно недоступен');
}

// Инициализация
updateUI();