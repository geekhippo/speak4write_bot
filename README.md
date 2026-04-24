# speak4write_bot

Бот для Telegram, который переводит голосовые сообщения, аудио и видео в текст с помощью модели `whisper-large-v3` от Groq API.

## Установка

Убедитесь, что у вас установлен Docker и Docker Compose.

Просто скопируйте и вставьте эту команду в терминал вашего сервера:

```bash
curl -sSL https://raw.githubusercontent.com/geekhippo/speak4write_bot/master/install.sh | bash
```

## Удаление бота

Чтобы полностью удалить бота и все связанные с ним файлы:

```bash
docker stop voice-bot
docker rm voice-bot
docker rmi voice-bot
rm -rf speak4write_bot
```

## Лицензия
MIT
