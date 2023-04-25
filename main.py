from PyQt5.QtWidgets import QMainWindow, QApplication, QSystemTrayIcon, QAction, QMenu, QStyle,qApp
from PyQt5.QtCore import Qt, QThread
import datetime, time, sys, os.path
from pyowm import OWM

from PyQt5 import QtCore, QtGui
from PyQt5.Qt import QIcon

from ui import Ui_MainWindow

wk = {'0': 'Monday',
      '1': 'Tuesday',
      '2': 'Wednesday',
      '3': 'Thursday',
      '4': 'Friday',
      '5': 'Saturday',
      '6': 'Sunday'
      }


sys._excepthook = sys.excepthook
def exception_hook(exctype, value, traceback):
    print(exctype, value, traceback)
    if exctype is KeyboardInterrupt:
        sys.exit(0)
    sys._excepthook(exctype, value, traceback)
    pass

sys.excepthook = exception_hook

def func(a: str):
    if len(a) == 1:
        return f'0{a}'
    else:
        return a

def unix_converter(unix):
    gt = time.gmtime(unix)
    return f'{func(str(int(gt.tm_hour) + 3))}:{func(str(gt.tm_min))}:{func(str(gt.tm_sec))}'

def func_weather(place):
    API = 'd8103ddb4c9d11d7f82ffad9cce5ee36'
    owm = OWM(API)
    try:
        monitoring = owm.weather_manager().weather_at_place(place)  # Вырвано из доков
        weather = monitoring.weather  # Тоже вырвано из доков
        temp = weather.temperature('celsius')['temp']  # Получение температуры по цельсия
        status = str(weather.detailed_status).capitalize()  # Краткий статус погоды
        sunrise = weather.sunrise_time()
        sunset = weather.sunset_time()
        status = f'{status}\nSunrise: {unix_converter(sunrise)}\nSunset: {unix_converter(sunset)}'
        wind = weather.wind().get('speed', 0)
        return f'{int(temp)}°C', status, wind
    except:
        return '', 'No internet connection\nor the city is incorrect\nPlease wait...', ''


class Widget(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        self.setAttribute(Qt.WA_TranslucentBackground)  # Убираем фон который выходит за круглые рамки, чтобы выглядело красиво
        self.setWindowFlags(
            Qt.Window
            | Qt.WindowStaysOnBottomHint
            | Qt.FramelessWindowHint
            | Qt.Tool
        )

        self._old_pos = None

        #self.setWindowOpacity(0.7)  # Прозрачность окна (от 0 до 1, float)

        self.pixmap = QtGui.QPixmap("Cloudy2.png")
        self.image.setPixmap(self.pixmap)
        self.image.resize(self.pixmap.width(), self.pixmap.height())

        self.btn_close.clicked.connect(qApp.quit)

        self.slider.valueChanged.connect(lambda: self.setWindowOpacity(self.slider.value()/100))

        if os.path.exists('assets') is False:
            os.mkdir('assets')

        if os.path.exists('assets/city.txt'):
            with open('assets/city.txt', 'r') as f:
                self.city.setText(f.read())
        else:
            self.city.setText('Moscow,RU')

        if os.path.exists('assets/opacity.txt'):
            with open('assets/opacity.txt', 'r') as f:
                value = f.read()
                slider_pos = int(float(value) * float(100))
                self.slider.setProperty('value', slider_pos)
                self.setWindowOpacity(float(value))

        self.thread_handler = Updater(str(self.city.text()))
        self.thread_handler.signal.connect(self.signal_handler)
        self.thread_handler.start()

        # Tray
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(self.style().standardIcon(QStyle.SP_ComputerIcon))
        self.tray_icon.setIcon(QIcon('Cloudy1.png'))

        show_action = QAction("Show", self)
        hide_action = QAction("Hide", self)
        close_action = QAction('Close', self)

        show_action.triggered.connect(self.show)
        hide_action.triggered.connect(self.hide)
        close_action.triggered.connect(qApp.quit)

        tray_menu = QMenu()
        tray_menu.addAction(show_action)
        tray_menu.addAction(hide_action)
        tray_menu.addAction(close_action)
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()

        if os.path.exists('assets/pos.txt'):
            with open('assets/pos.txt', 'r') as f:
                pos1, pos2 = f.read().split(', ')
                self.move(int(pos1), int(pos2))

        css = """QSlider::handle:horizontal {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #b4b4b4, stop:1 #8f8f8f);
    border: 1px solid #5c5c5c;
    width: 18px;
    margin: -2px 0; /* handle is placed by default on the contents rect of the groove. Expand outside the groove */
    border-radius: 1px;
}"""
        self.slider.setStyleSheet(css)





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

    def sliderMoveEvent(self, value):
        self.setWindowOpacity(value/100)

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
        elif value[0] == 'wind':
            self.wind.setText(f'{value[1]} m/s')
        elif value[0] == 'update':
            if os.path.exists('assets/city.txt'):
                f = open('assets/city.txt', 'r')
                if f.read() == str(self.city.text()):
                    pass
                else:
                    f.close()
                    f = open('assets/city.txt', 'w+')
                    f.write(str(self.city.text()))
                    self.thread_handler.city = str(self.city.text())
            else:
                with open('assets/city.txt', 'w') as f:
                    f.write(str(self.city.text()))

            with open('assets/pos.txt', 'w+') as f:
                f.write(str(self.pos()).replace('PyQt5.QtCore.QPoint(', '').replace(')', ''))

            with open('assets/opacity.txt', 'w+') as f:
                f.write(str(self.slider.value()/100))


class Updater(QThread):
    signal = QtCore.pyqtSignal(list)

    def __init__(self, city, parent=None):
        super(Updater, self).__init__(parent)
        self.city = city

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
            now_temperature, now_status, now_wind = func_weather(self.city)
            self.signal.emit(['temp', now_temperature])
            self.signal.emit(['status', str(now_status)])
            self.signal.emit(['wind', str(now_wind)])
            self.signal.emit(['update'])
            time.sleep(3)


# Запуск собственно
if __name__ == '__main__':
    app = QApplication([])

    w = Widget()
    w.show()

    app.exec()
