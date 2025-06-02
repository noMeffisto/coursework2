// Валидация формы регистрации
function validateRegistrationForm() {
    const form = document.getElementById('registration-form');
    if (!form) return;

    form.addEventListener('submit', function(e) {
        let isValid = true;
        const username = document.getElementById('id_username');
        const email = document.getElementById('id_email');
        const password1 = document.getElementById('id_password1');
        const password2 = document.getElementById('id_password2');

        // Валидация имени пользователя
        if (username.value.length < 3) {
            showError(username, 'Имя пользователя должно содержать минимум 3 символа');
            isValid = false;
        }

        // Валидация email
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(email.value)) {
            showError(email, 'Введите корректный email адрес');
            isValid = false;
        }

        // Валидация пароля
        if (password1.value.length < 8) {
            showError(password1, 'Пароль должен содержать минимум 8 символов');
            isValid = false;
        }

        // Проверка совпадения паролей
        if (password1.value !== password2.value) {
            showError(password2, 'Пароли не совпадают');
            isValid = false;
        }

        if (!isValid) {
            e.preventDefault();
        }
    });
}

// Валидация формы отзыва
function validateReviewForm() {
    const form = document.getElementById('review-form');
    if (!form) return;

    form.addEventListener('submit', function(e) {
        let isValid = true;
        const name = document.getElementById('name');
        const review = document.getElementById('review');

        if (name.value.length < 2) {
            showError(name, 'Имя должно содержать минимум 2 символа');
            isValid = false;
        }

        if (review.value.length < 10) {
            showError(review, 'Отзыв должен содержать минимум 10 символов');
            isValid = false;
        }

        if (!isValid) {
            e.preventDefault();
        }
    });
}

// Валидация формы контактов
function validateContactForm() {
    const form = document.getElementById('contact-form');
    if (!form) return;

    form.addEventListener('submit', function(e) {
        let isValid = true;
        const name = document.getElementById('name');
        const email = document.getElementById('email');
        const message = document.getElementById('message');

        if (name.value.length < 2) {
            showError(name, 'Имя должно содержать минимум 2 символа');
            isValid = false;
        }

        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(email.value)) {
            showError(email, 'Введите корректный email адрес');
            isValid = false;
        }

        if (message.value.length < 10) {
            showError(message, 'Сообщение должно содержать минимум 10 символов');
            isValid = false;
        }

        if (!isValid) {
            e.preventDefault();
        }
    });
}

// Вспомогательная функция для отображения ошибок
function showError(input, message) {
    const errorDiv = input.nextElementSibling || document.createElement('div');
    errorDiv.className = 'error-message';
    errorDiv.textContent = message;
    if (!input.nextElementSibling) {
        input.parentNode.insertBefore(errorDiv, input.nextSibling);
    }
    input.classList.add('error');
}

// Инициализация валидации
document.addEventListener('DOMContentLoaded', function() {
    validateRegistrationForm();
    validateReviewForm();
    validateContactForm();
}); 