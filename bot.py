import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters
import httpx
import os
from dotenv import load_dotenv

# Загрузка переменных из .env
load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GROQ_API_KEYS = os.getenv("GROQ_API_KEYS", "").split(",")
current_key_index = 0

def get_next_key():
    global current_key_index
    key = GROQ_API_KEYS[current_key_index]
    current_key_index = (current_key_index + 1) % len(GROQ_API_KEYS)
    return key

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Логируем, получили ли мы вообще сообщение
    msg = update.message
    # Выводим информацию обо всех полях, чтобы понять, какой именно тип Telegram прислал
    logging.info(f"Получено сообщение: {msg.to_dict()}")
    
    file_obj = msg.voice or msg.audio or msg.video or msg.document or msg.video_note
    
    if not file_obj:
        return

    # Скачивание файла
    file = await context.bot.get_file(file_obj.file_id)
    # Используем расширение .mp3 или .ogg, whisper поймет
    file_path = f"{file_obj.file_id}.ogg"
    await file.download_to_drive(file_path)

    try:
        # Попытка отправки с перебором всех ключей
        text = None
        for _ in range(len(GROQ_API_KEYS)):
            api_key = get_next_key()
            try:
                async with httpx.AsyncClient() as client:
                    with open(file_path, "rb") as f:
                        response = await client.post(
                            "https://api.groq.com/openai/v1/audio/transcriptions",
                            headers={"Authorization": f"Bearer {api_key.strip()}"},
                            files={"file": (file_path, f, "audio/ogg")},
                            data={"model": "whisper-large-v3"},
                            timeout=60.0
                        )
                
                result = response.json()
                text = result.get("text")
                if text:
                    break
            except Exception as e:
                logging.error(f"Ошибка при запросе с ключом: {e}")
                continue
        
        if text:
            await update.message.reply_text(f"Текст: {text}")
        else:
            await update.message.reply_text("Не удалось распознать текст.")
            
    except Exception as e:
        logging.error(f"Общая ошибка обработки: {e}")
        await update.message.reply_text("Произошла ошибка при обработке.")
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)

if __name__ == '__main__':
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    
    # Обработка любых сообщений для отладки
    application.add_handler(MessageHandler(filters.ALL, handle_voice))
    
    print("Бот запущен...")
    application.run_polling()
