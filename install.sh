#!/bin/bash

echo "🚀 Запуск установки @speak4write_bot..."

# 1. Проверка Docker
if ! command -v docker &> /dev/null; then
    echo "📦 Docker не найден. Устанавливаю..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
fi

# 2. Создание директории
mkdir -p speak4write_bot
cd speak4write_bot

# 3. Запрос данных
echo "📝 Нам понадобятся ваши ключи API."
read -p "Введите TELEGRAM_TOKEN: " TELEGRAM_TOKEN
read -p "Введите GROQ_API_KEYS (через запятую): " GROQ_API_KEYS

cat <<EOF > .env
TELEGRAM_TOKEN=$TELEGRAM_TOKEN
GROQ_API_KEYS=$GROQ_API_KEYS
EOF

# 4. Скачивание необходимых файлов
echo "📥 Скачиваю файлы бота..."
curl -sSL https://raw.githubusercontent.com/geekhippo/speak4write_bot/master/bot.py -o bot.py
curl -sSL https://raw.githubusercontent.com/geekhippo/speak4write_bot/master/Dockerfile -o Dockerfile
curl -sSL https://raw.githubusercontent.com/geekhippo/speak4write_bot/master/requirements.txt -o requirements.txt
curl -sSL https://raw.githubusercontent.com/geekhippo/speak4write_bot/master/docker-compose.yml -o docker-compose.yml

# 5. Запуск
echo "🏗️ Собираю и запускаю бота..."
# Пытаемся запустить через docker compose, но явно вызываем docker-compose если нужно
# Убираем -d, если он вызывает конфликт, и используем команду запуска без флагов в одну строку
docker compose build
docker compose up -d

echo "🎉 Готово! Бот @speak4write_bot запущен."
echo "Логи: docker compose logs -f"
