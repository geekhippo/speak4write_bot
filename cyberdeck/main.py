"""
CyberDeck — ESP32 + OLED дисплей на MicroPython
Экраны: Время | Погода | Курс валют | Система
"""

import network
import ntptime
import urequests
import json
import time
import machine
from machine import Pin, SoftI2C, Timer
import framebuf

# ═══════════════════════════════════════════
# НАСТРОЙКИ
# ═══════════════════════════════════════════
WIFI_SSID = "YOUR_WIFI_SSID"
WIFI_PASS = "YOUR_WIFI_PASS"

# OpenWeatherMap API (бесплатный ключ)
WEATHER_API_KEY = "your_openweathermap_api_key"
WEATHER_CITY = "Yekaterinburg"
WEATHER_LANG = "ru"

# Пины
OLED_SDA = 21
OLED_SCL = 22
BTN_NEXT = 4   # Кнопка переключения экрана
BTN_PREV = 5   # Кнопка назад
POT_PIN = 34   # Потенциометр (ADC)

# OLED параметры
OLED_WIDTH = 128
OLED_HEIGHT = 64
OLED_ADDR = 0x3C

# ═══════════════════════════════════════════
# OLED DRIVER (SSD1306)
# ═══════════════════════════════════════════
class SSD1306:
    def __init__(self, width, height, i2c, addr=0x3C):
        self.width = width
        self.height = height
        self.i2c = i2c
        self.addr = addr
        self.pages = height // 8
        self.buffer = bytearray(self.pages * width)
        self.fb = framebuf.FrameBuffer(self.buffer, width, height, framebuf.MONO_VLSB)
        self._init_display()

    def _cmd(self, cmd):
        self.i2c.writeto(self.addr, bytes([0x80, cmd]))

    def _init_display(self):
        cmds = [
            0xAE, 0xD5, 0x80, 0xA8, 0x3F, 0xD3, 0x00, 0x40,
            0x8D, 0x14, 0x20, 0x00, 0xA1, 0xC8, 0xDA, 0x12,
            0x81, 0xCF, 0xD9, 0xF1, 0xDB, 0x30, 0xA4, 0xA6, 0xAF
        ]
        for c in cmds:
            self._cmd(c)

    def show(self):
        self._cmd(0x21)
        self._cmd(0)
        self._cmd(self.width - 1)
        self._cmd(0x22)
        self._cmd(0)
        self._cmd(self.pages - 1)
        self.i2c.writeto(self.addr, b'\x40' + self.buffer)

    def fill(self, color):
        self.fb.fill(color)

    def text(self, text, x, y, color=1):
        self.fb.text(text, x, y, color)

    def hline(self, x, y, w, color=1):
        self.fb.hline(x, y, w, color)

    def rect(self, x, y, w, h, color=1):
        self.fb.rect(x, y, w, h, color)

    def fill_rect(self, x, y, w, h, color=1):
        self.fb.fill_rect(x, y, w, h, color)


# ═══════════════════════════════════════════
# CYBERDECK CLASS
# ═══════════════════════════════════════════
class CyberDeck:
    def __init__(self):
        # I2C для OLED
        self.i2c = SoftI2C(scl=Pin(OLED_SCL), sda=Pin(OLED_SDA))
        self.oled = SSD1306(OLED_WIDTH, OLED_HEIGHT, self.i2c, OLED_ADDR)

        # Кнопки
        self.btn_next = Pin(BTN_NEXT, Pin.IN, Pin.PULL_UP)
        self.btn_prev = Pin(BTN_PREV, Pin.IN, Pin.PULL_UP)

        # Потенциометр
        self.pot = machine.ADC(Pin(POT_PIN))
        self.pot.atten(machine.ADC.ATTN_11DB)
        self.pot.width(machine.ADC.WIDTH_12BIT)

        # WiFi
        self.wlan = network.WLAN(network.STA_IF)
        self.wifi_connected = False

        # Экраны
        self.screens = ["time", "weather", "currency", "system"]
        self.current_screen = 0

        # Кэш данных
        self.weather_data = None
        self.currency_data = None
        self.last_weather_update = 0
        self.last_currency_update = 0

        # Таймер обновления
        self.update_interval = 600  # 10 минут

    # ─── WiFi ───
    def connect_wifi(self):
        self.wlan.active(True)
        if not self.wlan.isconnected():
            self.oled.fill(0)
            self.oled.text("Connecting WiFi...", 0, 28)
            self.oled.show()
            self.wlan.connect(WIFI_SSID, WIFI_PASS)
            timeout = 20
            while not self.wlan.isconnected() and timeout > 0:
                time.sleep(1)
                timeout -= 1
        self.wifi_connected = self.wlan.isconnected()
        if self.wifi_connected:
            ntptime.settime()
        return self.wifi_connected

    # ─── Время ───
    def get_time_str(self):
        t = time.localtime()
        days = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
        months = ["Янв", "Фев", "Мар", "Апр", "Май", "Июн",
                  "Июл", "Авг", "Сен", "Окт", "Ноя", "Дек"]
        day_name = days[t[6]]
        month_name = months[t[1] - 1]
        return "{:02d}:{:02d}:{:02d}".format(t[3], t[4], t[5]), \
               "{} {} {}".format(t[2], month_name, t[0]), day_name

    # ─── Погода ───
    def fetch_weather(self):
        if not self.wifi_connected:
            return None
        try:
            url = ("http://api.openweathermap.org/data/2.5/weather"
                   "?q={}&appid={}&units=metric&lang={}").format(
                       WEATHER_CITY, WEATHER_API_KEY, WEATHER_LANG)
            resp = urequests.get(url, timeout=10)
            data = resp.json()
            resp.close()
            self.weather_data = {
                "temp": round(data["main"]["temp"]),
                "feels": round(data["main"]["feels_like"]),
                "desc": data["weather"][0]["description"],
                "humidity": data["main"]["humidity"],
                "wind": data["wind"]["speed"],
                "city": WEATHER_CITY
            }
            return self.weather_data
        except Exception as e:
            print("Weather error:", e)
            return None

    # ─── Курс валют ───
    def fetch_currency(self):
        if not self.wifi_connected:
            return None
        try:
            resp = urequests.get("https://www.cbr-xml-daily.ru/daily_json.js", timeout=10)
            data = resp.json()
            resp.close()
            self.currency_data = {
                "usd": data["Valute"]["USD"]["Value"],
                "eur": data["Valute"]["EUR"]["Value"],
                "cny": data["Valute"]["CNY"]["Value"],
                "date": data["Date"][:10]
            }
            return self.currency_data
        except Exception as e:
            print("Currency error:", e)
            return None

    # ─── Отрисовка экранов ───
    def draw_time_screen(self):
        self.oled.fill(0)
        time_str, date_str, day_name = self.get_time_str()

        # Заголовок
        self.oled.fill_rect(0, 0, 128, 10, 1)
        self.oled.text("   CYBERDECK", 0, 1, 0)

        # День недели
        self.oled.text(day_name, 45, 16)

        # Время (крупно)
        self.oled.text(time_str, 16, 30)

        # Дата
        self.oled.text(date_str, 20, 46)

        # Статус WiFi
        if self.wifi_connected:
            self.oled.text("WiFi OK", 0, 56)
        else:
            self.oled.text("No WiFi", 0, 56)

        self.oled.show()

    def draw_weather_screen(self):
        self.oled.fill(0)
        self.oled.fill_rect(0, 0, 128, 10, 1)
        self.oled.text("     WEATHER", 0, 1, 0)

        if self.weather_data is None:
            # Пробуем загрузить
            self.oled.text("Loading...", 30, 30)
            self.oled.show()
            self.fetch_weather()

        if self.weather_data:
            d = self.weather_data
            self.oled.text(d["city"], 25, 14)
            self.oled.hline(0, 22, 128, 1)

            # Температура крупно
            temp_str = "{}C".format(d["temp"])
            self.oled.text(temp_str, 35, 30)

            # Ощущается
            self.oled.text("Feels: {}C".format(d["feels"]), 20, 42)

            # Описание
            desc = d["desc"][:16]
            self.oled.text(desc, 10, 54)
        else:
            self.oled.text("No data", 35, 30)
            self.oled.text("Check WiFi", 25, 45)

        self.oled.show()

    def draw_currency_screen(self):
        self.oled.fill(0)
        self.oled.fill_rect(0, 0, 128, 10, 1)
        self.oled.text("    CURRENCY", 0, 1, 0)

        if self.currency_data is None:
            self.oled.text("Loading...", 30, 30)
            self.oled.show()
            self.fetch_currency()

        if self.currency_data:
            d = self.currency_data
            self.oled.text("Date: {}".format(d["date"][5:]), 10, 14)
            self.oled.hline(0, 22, 128, 1)

            self.oled.text("USD: {:.2f} RUB".format(d["usd"]), 10, 30)
            self.oled.text("EUR: {:.2f} RUB".format(d["eur"]), 10, 42)
            self.oled.text("CNY: {:.2f} RUB".format(d["cny"]), 10, 54)
        else:
            self.oled.text("No data", 35, 30)
            self.oled.text("Check WiFi", 25, 45)

        self.oled.show()

    def draw_system_screen(self):
        self.oled.fill(0)
        self.oled.fill_rect(0, 0, 128, 10, 1)
        self.oled.text("     SYSTEM", 0, 1, 0)

        # Информация о системе
        import gc
        free_mem = gc.mem_free()
        total_mem = gc.mem_alloc() + free_mem

        self.oled.text("Free mem: {}KB".format(free_mem // 1024), 5, 16)
        self.oled.text("Used mem: {}KB".format(gc.mem_alloc() // 1024), 5, 26)

        # WiFi статус
        if self.wifi_connected:
            ip = self.wlan.ifconfig()[0]
            self.oled.text("IP: {}".format(ip), 5, 36)
        else:
            self.oled.text("WiFi: disconnected", 5, 36)

        # Потенциометр
        pot_val = self.pot.read()
        self.oled.text("Pot: {}".format(pot_val), 5, 46)

        # Время работы
        uptime = time.ticks_diff(time.ticks_ms(), start_time) // 1000
        hours = uptime // 3600
        mins = (uptime % 3600) // 60
        self.oled.text("Up: {}h {}m".format(hours, mins), 5, 56)

        self.oled.show()

    # ─── Обработка кнопок ───
    def check_buttons(self):
        if self.btn_next.value() == 0:
            self.current_screen = (self.current_screen + 1) % len(self.screens)
            time.sleep_ms(300)  # Антидребезг
            return True
        if self.btn_prev.value() == 0:
            self.current_screen = (self.current_screen - 1) % len(self.screens)
            time.sleep_ms(300)
            return True
        return False

    # ─── Обновление данных ───
    def update_data(self):
        now = time.time()
        if now - self.last_weather_update > self.update_interval:
            self.fetch_weather()
            self.last_weather_update = now
        if now - self.last_currency_update > self.update_interval:
            self.fetch_currency()
            self.last_currency_update = now

    # ─── Главный цикл ───
    def run(self):
        # Подключение WiFi
        self.connect_wifi()

        # Первичная загрузка данных
        self.fetch_weather()
        self.fetch_currency()
        self.last_weather_update = time.time()
        self.last_currency_update = time.time()

        screen_drawers = {
            "time": self.draw_time_screen,
            "weather": self.draw_weather_screen,
            "currency": self.draw_currency_screen,
            "system": self.draw_system_screen
        }

        while True:
            # Проверка кнопок
            self.check_buttons()

            # Обновление данных по таймеру
            self.update_data()

            # Отрисовка текущего экрана
            screen_name = self.screens[self.current_screen]
            screen_drawers[screen_name]()

            time.sleep_ms(100)


# ═══════════════════════════════════════════
# ЗАПУСК
# ═══════════════════════════════════════════
start_time = time.ticks_ms()

deck = CyberDeck()
deck.run()
