import sys
import os

# Добавляем корневую директорию в sys.path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from PyQt5.QtWidgets import QApplication
from src.ui.login_window import LoginWindow

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = LoginWindow()
    window.show()
    sys.exit(app.exec_())