import sys
import os


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QLineEdit, QPushButton, QLabel
from src.core.auth import AuthManager
from src.ui.main_window import MainWindow

class LoginWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Music Analyzer - Login")
        self.auth_manager = AuthManager()
        self.setMinimumSize(400, 300)  
        self.init_ui()

    def init_ui(self):
        widget = QWidget()
        layout = QVBoxLayout()
        self.login_input = QLineEdit("Login")
        self.password_input = QLineEdit("Password")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.error_label = QLabel("")
        self.error_label.setStyleSheet("color: red")
        login_button = QPushButton("Login")
        login_button.clicked.connect(self.handle_login)
        layout.addWidget(self.login_input)
        layout.addWidget(self.password_input)
        layout.addWidget(self.error_label)
        layout.addWidget(login_button)
        widget.setLayout(layout)
        self.setCentralWidget(widget)

    def handle_login(self):
        login = self.login_input.text()
        password = self.password_input.text()
        user = self.auth_manager.login(login, password)
        if user:
            self.main_window = MainWindow(user["role"])
            self.main_window.show()
            self.close()
        else:
            self.error_label.setText("Login failed! Invalid username or password.")