# 🤖 CyberDeck — ESP32 + OLED на MicroPython

Компактная информационная панель на базе ESP32 с OLED дисплеем.

## Возможности

- 🕐 **Время и дата** — NTP синхронизация
- 🌤 **Погода** — OpenWeatherMap API
- 💱 **Курс валют** — USD, EUR, CNY от ЦБ РФ
- 📊 **Системная информация** — память, IP, аптайм

## Компоненты

- ESP32 DevKit
- OLED дисплей SSD1306 (128x64, I2C)
- 2 кнопки (переключение экранов)
- Потенциометр (ADC)

## Подключение

```
ESP32    →    OLED SSD1306
──────────────────────────
GPIO 21  →    SDA
GPIO 22  →    SCL
3.3V     →    VCC
GND      →    GND

Кнопка NEXT  →  GPIO 4  →  GND
Кнопка PREV  →  GPIO 5  →  GND
Потенциометр →  GPIO 34 (ADC)
```

## Установка

1. Установи MicroPython на ESP32:
```bash
esptool.py --chip esp32 --port /dev/ttyUSB0 erase_flash
esptool.py --chip esp32 --port /dev/ttyUSB0 write_flash -z 0x1000 esp32-20220618-v1.19.1.bin
```

2. Загрузи файлы на ESP32:
```bash
ampy --port /dev/ttyUSB0 put main.py
ampy --port /dev/ttyUSB0 put config.json
```

3. Отредактируй `config.json` — укажи WiFi и API ключ

4. Перезагрузи ESP32

## Получение API ключа погоды

1. Перейди на [openweathermap.org](https://openweathermap.org/api)
2. Зарегистрируйся (бесплатно)
3. Создай API key в личном кабинете
4. Вставь ключ в `config.json`

## Управление

- **Кнопка NEXT** — следующий экран
- **Кнопка PREV** — предыдущий экран
- **Потенциометр** — показание на системном экране

## Экраны

| Экран | Что показывает |
|-------|----------------|
| Время | Часы, дата, день недели, статус WiFi |
| Погода | Температура, ощущается, описание, влажность |
| Валюта | Курс USD, EUR, CNY к рублю |
| Система | Память, IP, аптайм, показание потенциометра |
