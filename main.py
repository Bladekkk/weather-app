from PyQt5.QtWidgets import QMainWindow, QApplication
from PyQt5.QtCore import Qt, QThread
import datetime, time
from pyowm import OWM

from PyQt5 import QtCore, QtGui

from ui import Ui_MainWindow

wk = {'0': 'Monday',
      '1': 'Tuesday',
      '2': 'Wednesday',
      '3': 'Thursday',
      '4': 'Friday',
      '5': 'Saturday',
      '6': 'Sunday'
      }


def func_weather():
    API = 'd8103ddb4c9d11d7f82ffad9cce5ee36'
    try:
        owm = OWM(API)
        place = 'Северодвинск'  # Задание места, по дефолту поставил Севск, но в будущем будет зависеть от настроек пользователя
        monitoring = owm.weather_manager().weather_at_place(place)  # Вырвано из доков
        weather = monitoring.weather  # Тоже вырвано из доков
        temp = weather.temperature('celsius')['temp']  # Получение температуры по цельсия
        status = weather.detailed_status  # Краткий статус погоды, типо "Облачно"
    except:
        temp = ''
        status = 'Не найдено подключение к интернету'
    return temp, status


def func(a: str):
    if len(a) == 1:
        return f'0{a}'
    else:
        return a


class Widget(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        self.setWindowFlags(Qt.FramelessWindowHint)  # Убираем системные рамки + кнопки: закрыть, свернуть
        self.setAttribute(Qt.WA_TranslucentBackground)  # Убираем фон который выходит за круглые рамки, чтобы выглядело красиво

        self._old_pos = None

        self.setWindowOpacity(0.75)  # Прозрачность окна (от 0 до 1, float)

        self.pixmap = QtGui.QPixmap("Cloudy2.png")
        self.image.setPixmap(self.pixmap)
        self.image.resize(self.pixmap.width(), self.pixmap.height())

        self.btn_close.clicked.connect(self.close)

        self.thread_handler = Updater(True)
        self.thread_handler.signal.connect(self.signal_handler)
        self.thread_handler.start()

    # Следующие функции для того чтобы переносить окно за любое место
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._old_pos = event.pos()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._old_pos = None

    def mouseMoveEvent(self, event):
        if not self._old_pos:
            return
        delta = event.pos() - self._old_pos
        self.move(self.pos() + delta)

    def signal_handler(self, value: list) -> None:
        if value[0] == 'time':
            self.time.setText(value[1])
        elif value[0] == 'date':
            self.date.setText(value[1])
        elif value[0] == 'weekday':
            self.weekday.setText(value[1])
        elif value[0] == 'temp':
            self.temperature.setText(value[1])
        elif value[0] == 'status':
            self.weather.setText(value[1])


class Updater(QThread):
    signal = QtCore.pyqtSignal(list)

    def __init__(self, status, parent=None):
        super(Updater, self).__init__(parent)
        self.status = status

    def run(self):
        self.signal.emit(['started'])
        while True:
            now = datetime.datetime.now()
            now_time = f'{func(str(now.hour))}:{func(str(now.minute))}'
            self.signal.emit(['time', now_time])
            now_date = f'{func(str(now.day))}.{func(str(now.month))}.{func(str(now.year))}'
            self.signal.emit(['date', now_date])
            now_weekday = str(now.weekday())
            self.signal.emit(['weekday', wk[now_weekday]])
            now_temperature, now_status = func_weather()
            self.signal.emit(['temp', f"{int(now_temperature)}°C"])
            self.signal.emit(['status', str(now_status).capitalize()])
            time.sleep(3)


# Запуск собственно
if __name__ == '__main__':
    app = QApplication([])

    w = Widget()
    w.show()

    app.exec()
