#!/bin/bash

echo "🚀 Запуск установки @speak4write_bot..."

# 1. Проверка и установка Docker
if ! command -v docker &> /dev/null; then
    echo "📦 Docker не найден. Устанавливаю..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    sudo usermod -aG docker $USER
    echo "✅ Docker установлен. Перезайдите в систему, чтобы изменения вступили в силу."
fi

# 2. Создание рабочей директории
mkdir -p speak4write_bot
cd speak4write_bot

# 3. Запрос данных у пользователя
echo "📝 Нам понадобятся ваши ключи API."
read -p "Введите TELEGRAM_TOKEN: " TELEGRAM_TOKEN
read -p "Введите GROQ_API_KEYS (через запятую): " GROQ_API_KEYS

cat <<EOF > .env
TELEGRAM_TOKEN=$TELEGRAM_TOKEN
GROQ_API_KEYS=$GROQ_API_KEYS
EOF

# 4. Скачивание файлов бота (заглушка: предполагается, что файлы уже в репозитории)
# Здесь должен быть git clone ...
echo "📥 Файлы бота готовы."

# 5. Сборка и запуск через docker-compose
echo "🏗️ Собираю и запускаю контейнер..."
docker compose up -d --build

echo "🎉 Готово! Бот @speak4write_bot запущен в фоновом режиме."
echo "Логи можно посмотреть командой: docker compose logs -f"
