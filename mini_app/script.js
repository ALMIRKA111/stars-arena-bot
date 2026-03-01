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
}

// Вкладки
const pvpTab = document.getElementById('pvp-tab');
const profileTab = document.getElementById('profile-tab');
const pvpBtn = document.getElementById('pvp-btn');
const profileBtn = document.getElementById('profile-btn');

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

// ===== ПОПОЛНЕНИЕ (РАБОЧАЯ ВЕРСИЯ) =====
const depositInput = document.getElementById('deposit-amount');
const depositBtn = document.getElementById('deposit-btn');

depositBtn.addEventListener('click', () => {
    const amount = parseInt(depositInput.value);

    if (!amount || amount < 10) {
        tg.showAlert('❌ Минимальная сумма: 10⭐');
        return;
    }

    // Отправляем данные боту
    tg.sendData(JSON.stringify({
        action: 'deposit',
        amount: amount
    }));

    // Показываем сообщение и закрываем
    tg.showPopup({
        title: 'Запрос отправлен',
        message: `Ожидайте счёт от бота на ${amount}⭐`,
        buttons: [{ type: 'ok' }]
    });

    tg.close();
});

// Инициализация
updateUI();