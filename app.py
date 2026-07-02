import os
import subprocess
import threading
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Label
from textual.containers import VerticalScroll

class DashboardApp(App):
    BINDINGS = [("q", "quit", "Quit")]
    CSS = """
    Label { padding: 1; border: solid green; margin: 1; }
    """

    def compose(self) -> ComposeResult:
        yield Header()
        yield VerticalScroll(
            Label("Нагрузка: Загрузка...", id="load"),
            Label("Fail2Ban: Загрузка...", id="f2b"),
            Label("Скорость интернета: Загрузка...", id="speed"),
            id="main-container"
        )
        yield Footer()

    def on_mount(self) -> None:
        self.set_interval(2.0, self.update_stats)
        self.set_interval(1800.0, self.update_speed)
        threading.Thread(target=self.update_speed, daemon=True).start()

    def update_stats(self) -> None:
        load = os.getloadavg()
        self.query_one("#load", Label).update(f"Нагрузка (1, 5, 15 мин): {load[0]:.2f}, {load[1]:.2f}, {load[2]:.2f}")
        try:
            res = subprocess.check_output(["sudo", "fail2ban-client", "status", "sshd"], text=True)
            banned = [line for line in res.splitlines() if "Currently banned" in line][0].split(":")[-1].strip()
            self.query_one("#f2b", Label).update(f"Fail2Ban (sshd) - Забанено сейчас: {banned}")
        except Exception:
            self.query_one("#f2b", Label).update("Fail2Ban: Ошибка доступа")

    def update_speed(self) -> None:
        self.query_one("#speed", Label).update("Скорость: Тестирование...")
        try:
            # Запуск speedtest-cli
            res = subprocess.check_output(["speedtest-cli", "--simple"], text=True)
            self.query_one("#speed", Label).update(f"Скорость интернета:\n{res.strip()}")
        except Exception as e:
            self.query_one("#speed", Label).update("Скорость: Ошибка теста")

if __name__ == "__main__":
    app = DashboardApp()
    app.run()
EOF
