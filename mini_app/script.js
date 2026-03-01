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
let selectedAmount = null;
let myCurrentBet = null;

// 15 уникальных цветов
const colors = [
    '🔴 Красный', '🔵 Синий', '🟢 Зеленый', '🟡 Желтый', '🟣 Фиолетовый',
    '🟠 Оранжевый', '⚫️ Черный', '⚪️ Белый', '🟤 Коричневый', '💗 Розовый',
    '🩵 Голубой', '💚 Лайм', '🧡 Мандарин', '🤎 Шоколад', '🩶 Серый'
];

// Получаем пользователя
if (tg.initDataUnsafe && tg.initDataUnsafe.user) {
    currentUser = tg.initDataUnsafe.user;
    document.getElementById('username').textContent = currentUser.first_name || 'Игрок';

    // Генерируем уникальную реферальную ссылку
    const refLink = `https://t.me/${tg.initDataUnsafe.user?.username || 'bot'}?start=ref_${currentUser.id}`;
    document.getElementById('partner-link').textContent = refLink;
} else {
    currentUser = { id: 123456789, first_name: 'Тест' };
    document.getElementById('username').textContent = 'Тестовый режим';
    document.getElementById('partner-link').textContent = 'https://t.me/test_bot?start=ref_123';
}

// ===== ОСНОВНЫЕ ФУНКЦИИ =====
function updateUI() {
    document.getElementById('balance').textContent = mockData.balance.toFixed(0);
    document.getElementById('bank-value').textContent = mockData.bank.toFixed(0);
    document.getElementById('profile-balance').textContent = mockData.balance.toFixed(0);
    document.getElementById('withdraw-balance').textContent = mockData.balance.toFixed(0);

    updatePlayersList();
    updatePartnerUI();

    const betInfo = document.getElementById('bet-info');
    const placeBetBtn = document.getElementById('place-bet');

    if (myCurrentBet) {
        betInfo.style.display = 'flex';
        placeBetBtn.style.display = 'block';
        document.getElementById('bet-amount-display').textContent = myCurrentBet.amount;
        document.getElementById('bet-percent-display').textContent = myCurrentBet.percent.toFixed(2);
        document.getElementById('bet-color-display').textContent = myCurrentBet.color;
    } else {
        betInfo.style.display = 'none';
        placeBetBtn.style.display = 'none';
    }
}

function updatePlayersList() {
    const playersList = document.getElementById('players-list');
    playersList.innerHTML = '';

    if (mockData.players.length === 0) {
        playersList.innerHTML = '<div class="empty-players">Пока нет ставок</div>';
        return;
    }

    const sortedPlayers = [...mockData.players].sort((a, b) => b.percent - a.percent);

    sortedPlayers.forEach((player, index) => {
        const playerDiv = document.createElement('div');
        playerDiv.className = 'player-item';

        if (player.isYou) {
            playerDiv.classList.add('you');
        }

        playerDiv.innerHTML = `
            <span class="player-number">#${index + 1}</span>
            <span class="player-color">${player.color}</span>
            <span class="player-percent">${player.percent.toFixed(2)}%</span>
        `;
        playersList.appendChild(playerDiv);
    });
}

function updatePartnerUI() {
    document.getElementById('partner-total').textContent = mockData.partner.totalEarned + '⭐';
    document.getElementById('partner-refs').textContent = mockData.partner.referrals + ' ЧЕЛ.';
    document.getElementById('partner-active').textContent = mockData.partner.activeReferrals + ' ЧЕЛ.';
    document.getElementById('partner-available').textContent = mockData.partner.availableToWithdraw + '⭐';

    const withdrawBtn = document.getElementById('partner-withdraw-btn');
    if (mockData.partner.availableToWithdraw >= 150) {
        withdrawBtn.disabled = false;
        withdrawBtn.style.opacity = '1';
    } else {
        withdrawBtn.disabled = true;
        withdrawBtn.style.opacity = '0.5';
    }
}

// ===== НАВИГАЦИЯ =====
const pvpTab = document.getElementById('pvp-tab');
const profileTab = document.getElementById('profile-tab');
const pvpBtn = document.getElementById('pvp-btn');
const profileBtn = document.getElementById('profile-btn');

pvpBtn.addEventListener('click', () => {
    pvpTab.style.display = 'block';
    profileTab.style.display = 'none';
    pvpBtn.classList.add('active');
    profileBtn.classList.remove('active');
    hideAllScreens();
});

profileBtn.addEventListener('click', () => {
    pvpTab.style.display = 'none';
    profileTab.style.display = 'block';
    profileBtn.classList.add('active');
    pvpBtn.classList.remove('active');
    hideAllScreens();
    updateProfileStats();
});

function hideAllScreens() {
    document.getElementById('deposit-screen').style.display = 'none';
    document.getElementById('withdraw-screen').style.display = 'none';
    document.getElementById('partner-screen').style.display = 'none';
}

function updateProfileStats() {
    document.getElementById('profile-balance').textContent = mockData.balance.toFixed(0);
    document.getElementById('profile-games').textContent = mockData.players.length;
    const wins = mockData.players.filter(p => p.isYou && p.isWinner).length;
    document.getElementById('profile-wins').textContent = wins;
    const winrate = mockData.players.length > 0 ? ((wins / mockData.players.length) * 100).toFixed(1) : 0;
    document.getElementById('profile-winrate').textContent = winrate + '%';
}

// ===== ПОПОЛНЕНИЕ =====
function showDeposit() {
    hideAllScreens();
    document.getElementById('deposit-screen').style.display = 'flex';
}

function hideDeposit() {
    document.getElementById('deposit-screen').style.display = 'none';
}

function processDeposit() {
    const amount = parseInt(document.getElementById('deposit-amount').value);

    if (!amount || amount < 10) {
        tg.showAlert('❌ Минимальная сумма пополнения: 10⭐');
        return;
    }

    mockData.balance += amount;
    updateUI();
    hideDeposit();
    tg.showAlert(`✅ Пополнено ${amount}⭐`);
}

// Выбор метода пополнения
document.querySelectorAll('.payment-method').forEach(btn => {
    btn.addEventListener('click', () => {
        document.querySelectorAll('.payment-method').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
    });
});

// ===== ВЫВОД =====
function showWithdraw() {
    hideAllScreens();
    document.getElementById('withdraw-screen').style.display = 'flex';
    document.getElementById('withdraw-balance').textContent = mockData.balance;
}

function hideWithdraw() {
    document.getElementById('withdraw-screen').style.display = 'none';
}

function setMaxWithdraw() {
    document.getElementById('withdraw-amount').value = mockData.balance;
}

function processWithdraw() {
    let amount = parseInt(document.getElementById('withdraw-amount').value);

    if (!amount || amount < 100) {
        tg.showAlert('❌ Минимальная сумма вывода: 100⭐');
        return;
    }

    if (amount > mockData.balance) {
        tg.showAlert('❌ Недостаточно средств');
        return;
    }

    // Вычитаем комиссию 2%
    const commission = Math.floor(amount * 0.02);
    const finalAmount = amount - commission;

    mockData.balance -= amount;
    updateUI();
    hideWithdraw();

    tg.showAlert(`✅ Заявка на вывод ${finalAmount}⭐ создана\nКомиссия: ${commission}⭐`);
}

function showTransactions() {
    tg.showAlert('📋 История транзакций будет доступна позже');
}

// ===== ПАРТНЁРСКАЯ ПРОГРАММА =====
function showPartner() {
    hideAllScreens();
    document.getElementById('partner-screen').style.display = 'flex';
}

function hidePartner() {
    document.getElementById('partner-screen').style.display = 'none';
}

function copyPartnerLink() {
    const link = document.getElementById('partner-link').textContent;
    navigator.clipboard.writeText(link);
    tg.showAlert('✅ Ссылка скопирована!');
}

function withdrawPartner() {
    if (mockData.partner.availableToWithdraw < 150) {
        tg.showAlert('❌ Минимальная сумма вывода: 150⭐');
        return;
    }

    mockData.balance += mockData.partner.availableToWithdraw;
    mockData.partner.availableToWithdraw = 0;
    updateUI();
    tg.showAlert('✅ Средства зачислены на баланс');
}

// ===== ПОДДЕРЖКА И ПРОМОКОДЫ =====
function showSupport() {
    tg.showAlert('🆘 Поддержка: @support_bot');
}

function showPromo() {
    const promo = prompt('Введите промокод:');
    if (promo) {
        tg.showAlert('✅ Промокод активирован! Получено 50⭐');
        mockData.balance += 50;
        updateUI();
    }
}

// ===== ИГРОВАЯ ЛОГИКА =====
const amountInput = document.getElementById('bet-amount-input');
const okBtn = document.getElementById('ok-btn');

okBtn.addEventListener('click', () => {
    const amount = parseInt(amountInput.value);

    if (!amount || amount <= 0) {
        tg.showAlert('❌ Введи корректную сумму!');
        return;
    }

    if (amount > mockData.balance) {
        tg.showAlert('❌ Недостаточно средств!');
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
    document.getElementById('place-bet').style.display = 'block';

    amountInput.value = '';

    if (tg.HapticFeedback) {
        tg.HapticFeedback.impactOccurred('light');
    }
});

document.getElementById('place-bet').addEventListener('click', () => {
    if (!myCurrentBet) return;

    const newPlayer = {
        color: myCurrentBet.color,
        amount: myCurrentBet.amount,
        percent: 0,
        isYou: true,
        isWinner: false
    };
    mockData.players.push(newPlayer);

    mockData.bank += myCurrentBet.amount;
    mockData.balance -= myCurrentBet.amount;

    mockData.players.forEach(player => {
        player.percent = (player.amount / mockData.bank) * 100;
    });

    const you = mockData.players.find(p => p.isYou);
    if (you) {
        myCurrentBet.percent = you.percent;
    }

    document.getElementById('place-bet').style.display = 'none';
    myCurrentBet = null;
    selectedAmount = null;

    updateUI();
    spinWheel();

    // Имитация дохода для партнёрки
    mockData.partner.totalEarned += Math.floor(myCurrentBet?.amount * 0.1) || 0;
    mockData.partner.availableToWithdraw += Math.floor(myCurrentBet?.amount * 0.1) || 0;
    updatePartnerUI();
});

function spinWheel() {
    const wheel = document.getElementById('wheel');
    if (!wheel) return;

    const spins = 5 + Math.floor(Math.random() * 5);
    const totalDegrees = spins * 360;

    wheel.style.transition = 'transform 3s cubic-bezier(0.25, 0.1, 0.15, 1)';
    wheel.style.transform = `rotate(${totalDegrees}deg)`;

    setTimeout(() => {
        const total = mockData.players.reduce((sum, p) => sum + p.amount, 0);
        const random = Math.random() * total;

        let cumulative = 0;
        let winner = null;
        for (const player of mockData.players) {
            cumulative += player.amount;
            if (random <= cumulative) {
                winner = player;
                break;
            }
        }

        if (winner) {
            mockData.players.forEach(p => p.isWinner = false);
            winner.isWinner = true;
            showWinner(winner);
        }

        setTimeout(() => {
            wheel.style.transition = 'none';
        }, 3000);
    }, 3000);
}

function showWinner(winner) {
    const popup = document.createElement('div');
    popup.className = 'result-popup';
    popup.innerHTML = `
        <div class="result-content">
            <div class="result-title">🏆 ПОБЕДИТЕЛЬ</div>
            <div class="result-text">
                Цвет: ${winner.color}<br>
                Ставка: ${winner.amount}⭐<br>
                Шанс: ${winner.percent.toFixed(2)}%
            </div>
            <button class="result-ok" onclick="this.parentElement.parentElement.remove()">OK</button>
        </div>
    `;
    document.body.appendChild(popup);
    popup.style.display = 'flex';

    if (tg.HapticFeedback) {
        tg.HapticFeedback.notification('success');
    }
}

// Инициализация
updateUI();

// Кнопка Telegram
tg.MainButton.setText('🔄 Обновить');
tg.MainButton.onClick(updateUI);
tg.MainButton.show();