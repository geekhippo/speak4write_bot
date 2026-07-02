# Пошаговый гайд: Reticulum на Raspberry Pi + Heltec V3

## Что понадобится

- Raspberry Pi (любая модель с USB и WiFi)
- Heltec V3 (LoRa 868MHz)
- USB-кабель для Heltec V3
- Android-телефон
- ПК для первоначальной настройки Pi

---

## Шаг 1: Прошивка Heltec V3 как RNode

RNode — это специальная прошивка для LoRa-устройств, созданная специально для Reticulum.

```bash
# На ПК (или прямо на Pi) устанавливаем Reticulum
pip install rns

# Подключаем Heltec V3 по USB

# Запускаем автоустановку прошивки RNode
rnodeconf --autoinstall
```

Утилита задаст вопросы:
1. Выбрать плату → **Heltec V3**
2. Частота → **868 MHz** (для России/Европы)
3. Мощность → оставить по умолчанию (20 dBm)
4. Bandwidth → **125 kHz** (стандарт для дальней связи)
5. Spreading Factor → **SF8** (баланс скорости/дальности)

После прошивки Heltec V3 станет RNode — устройством, которое Reticulum понимает нативно.

**Проверка:**
```bash
rnodeconf /dev/ttyUSB0 --info
```
Должно показать информацию об RNode.

---

## Шаг 2: Установка Reticulum на Raspberry Pi

```bash
# Обновляем систему
sudo apt update && sudo apt upgrade -y

# Ставим зависимости
sudo apt install python3 python3-pip python3-cryptography python3-pyserial -y

# Устанавливаем Reticulum
pip install rns --break-system-packages

# Устанавливаем LXMF (мессенджинг-протокол)
pip install lxmf --break-system-packages

# Проверяем
rnsd --version
```

---

## Шаг 3: Настройка Reticulum на Pi

Запускаем Reticulum один раз, чтобы создался конфиг:

```bash
rnsd
# Нажимаем Ctrl+C — конфиг создан
```

Редактируем конфиг:

```bash
nano ~/.reticulum/config
```

Добавляем два интерфейса — LoRa (через RNode) и TCP-сервер (для телефона по WiFi):

```ini
# === LoRa через RNode (USB) ===
[[RNode Interface]]
  type = RNodeInterface
  port = /dev/ttyUSB0
  frequency = 868000000
  bandwidth = 125000
  spreadingfactor = 8
  codingrate = 5
  txpower = 20
  # Настройки специфичные для Heltec V3

# === TCP-сервер для телефона по WiFi ===
[[TCP Server Interface]]
  type = TCPServerInterface
  listen_ip = 0.0.0.0
  listen_port = 4242
  # Телефон подключится к Pi:4242 по WiFi
```

**Важно:** Убедись что `/dev/ttyUSB0` — это твой Heltec V3. Проверить можно:
```bash
ls /dev/ttyUSB* /dev/ttyACM*
# Или после подключения:
dmesg | tail -5
```

---

## Шаг 4: Запуск Reticulum на Pi

```bash
# Запускаем как демон
rnsd &
```

Проверяем:
```bash
rnstatus
```
Должно показать оба интерфейса (RNode + TCP Server) со статусом Active.

---

## Шаг 5: Установка LXMF-бота на Pi

Создаём простого бота, который отвечает на сообщения:

```bash
mkdir -p ~/reticulum-bot
nano ~/reticulum-bot/bot.py
```

```python
#!/usr/bin/env python3
"""
Reticulum LXMF Bot — Погода, курсы,_ping
"""
import RNS
import LXMF
import time
import requests
import json

# Идентификация бота
bot_name = "PiBot"

# Callback при получении сообщения
def message_received(message):
    sender = RNS.hexrep(message.source_hash, delimit=False)
    text = message.content.decode('utf-8').strip()
    print(f"Сообщение от {sender[:16]}: {text}")
    
    response = ""
    text_lower = text.lower()
    
    if text_lower == "ping":
        response = "🏓 Понг! PiBot жив."
    
    elif text_lower in ["погода", "weather"]:
        try:
            r = requests.get(
                "https://api.open-meteo.com/v1/forecast?"
                "latitude=56.83&longitude=60.60&current_weather=true",
                timeout=10
            )
            data = r.json()["current_weather"]
            response = (
                f"🌤 Погода в Екатеринбурге:\n"
                f"🌡 Температура: {data['temperature']}°C\n"
                f"💨 Ветер: {data['windspeed']} км/ч\n"
                f"📏 Давление: {data.get('weathercode', 'н/д')}"
            )
        except Exception as e:
            response = f"Ошибка получения погоды: {e}"
    
    elif text_lower in ["курс", "rate", "usd"]:
        try:
            r = requests.get(
                "https://open.er-api.com/v6/latest/USD",
                timeout=10
            )
            rates = r.json()["rates"]
            rub = rates.get("RUB", "н/д")
            eur = rates.get("EUR", "н/д")
            response = (
                f"💱 Курсы валют (USD):\n"
                f"🇷🇺 RUB: {rub}\n"
                f"🇪🇺 EUR: {eur}"
            )
        except Exception as e:
            response = f"Ошибка получения курсов: {e}"
    
    elif text_lower in ["help", "помощь", "?"]:
        response = (
            "📋 Команды PiBot:\n"
            "• ping — проверить связь\n"
            "• погода — прогноз для Екб\n"
            "• курс — курсы валют\n"
            "• help — эта справка"
        )
    
    else:
        response = f"Неизвестная команда: '{text}'. Введите 'help' для справки."
    
    # Отправляем ответ
    if response:
        send_message(message.source_hash, response)


def send_message(destination_hash, text):
    """Отправить LXMF-сообщение."""
    try:
        dest = bytes.fromhex(destination_hash)
        lxm = LXMF.LXMessage(
            dest,
            lxmf_destination,
            text,
            desired_method=LXMF.LXMessage.DIRECT
        )
        lxmf_router.handle_outbound(lxm)
        print(f"Отправлено → {destination_hash[:16]}: {text[:50]}")
    except Exception as e:
        print(f"Ошибка отправки: {e}")


# === Инициализация ===
print("Инициализация Reticulum...")
reticulum = RNS.Reticulum()

# Создаём Identity для бота
bot_identity = RNS.Identity()

# Создаём LXMF роутер
lxmf_router = LXMF.LXMFRouter(
    identity=bot_identity,
    storagepath="~/.lxmfbot"
)

# Создаём destination для приёма сообщений
lxmf_destination = lxmf_router.register_delivery_identity(
    bot_identity,
    display_name=bot_name
)

# Подписываемся на входящие
lxmf_router.register_delivery_callback(message_received)

print(f"PiBot запущен! Адрес: {RNS.hexrep(lxmf_destination.hash, delimit=False)}")
print("Ожидание сообщений...")
print("Добавь этот адрес в Sideband для связи.")

# Держим процесс живым
while True:
    time.sleep(1)
```

Делаем исполняемым и запускаем:
```bash
chmod +x ~/reticulum-bot/bot.py
python3 ~/reticulum-bot/bot.py
```

**При первом запуске бот выдаст свой адрес** — длинную hex-строку. Запиши его!

---

## Шаг 6: Установка Sideband на Android

1. Скачай APK: [github.com/markqvist/Sideband/releases/latest](https://github.com/markqvist/Sideband/releases/latest)
2. Установи (разреши установку из неизвестных источников)
3. Открой Sideband

### Настройка подключения к Pi

В Sideband: **Настройки → Соединения → Добавить**

Если телефон и Pi в одной WiFi-сети:
- **Тип:** TCP Client
- **Хост:** IP-адрес Pi в локальной сети (найди через `hostname -I`)
- **Порт:** 4242

### Добавление бота

1. В Sideband → **Контакты → Добавить**
2. Вставь hex-адрес бота из Шага 5
3. Имя: `PiBot`
4. Отправь сообщение `ping`
5. Должен прийти ответ `🏓 Понг!`

---

## Шаг 7: Подключение Heltec V3 к телефону

Для работы по LoRa напрямую (без Pi):

1. Подключи Heltec V3 (с прошивкой RNode) к телефону через USB OTG
2. В Sideband → **Настройки → Соединения → Добавить**
3. **Тип:** RNode
4. **Порт:** /dev/ttyUSB0 (или как определится)
5. Sideband начнёт общаться по LoRa

---

## Шаг 8: Автозапуск на Pi

```bash
# Создаём systemd-сервис для Reticulum
sudo nano /etc/systemd/system/rnsd.service
```

```ini
[Unit]
Description=Reticulum Network Stack
After=network.target

[Service]
Type=simple
User=pi
ExecStart=/usr/bin/python3 -m RNS
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# Создаём сервис для бота
sudo nano /etc/systemd/system/reticulum-bot.service
```

```ini
[Unit]
Description=Reticulum LXMF Bot
After=rnsd.service

[Service]
Type=simple
User=pi
ExecStart=/usr/bin/python3 /home/pi/reticulum-bot/bot.py
WorkingDirectory=/home/pi/reticulum-bot
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable rnsd reticulum-bot
sudo systemctl start rnsd reticulum-bot

# Проверка
sudo systemctl status rnsd reticulum-bot
```

---

## Шаг 9: Установка Nomad Network на Pi (опционально)

Nomad Network — это BBS/веб-узел в Reticulum-сети. Аналог Room Server из MeshCore, но мощнее.

```bash
pip install nomadnet --break-system-packages

# Запуск
nomadnet
```

Nomad Network создаёт узел, который можно просматривать из Sideband или другого клиента. Там можно публиковать страницы, чаты, файлы.

---

## Сводка портов и адресов

| Элемент | Адрес/порт |
|---|---|
| Pi WiFi IP | `192.168.x.x` (узнай через `hostname -I`) |
| Reticulum TCP Server | `0.0.0.0:4242` |
| RNode (LoRa) | `/dev/ttyUSB0` |
| Бот LXMF адрес | выдаётся при первом запуске |

---

## Проверка работы

```bash
# Статус Reticulum
rnstatus

# Соседи в сети
rnprobe

# Логи
journalctl -u rnsd -f
journalctl -u reticulum-bot -f
```

---

## Возможные проблемы

1. **Heltec V3 не определяется** → проверь USB-кабель, попробуй `/dev/ttyACM0`
2. **Телефон не подключается к Pi** → проверь что оба в одной WiFi-сети, порт 4242 открыт
3. **Бот не отвечает** → проверь что адрес бота правильно скопирован в Sideband
4. **LoRa-соседей нет** → это нормально если ты один в районе, Pi и Heltec должны видеть друг друга
