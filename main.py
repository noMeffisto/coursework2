import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QCoreApplication

from ui.main_window import MainWindow
from core.player import AudioPlayer 

QCoreApplication.setOrganizationName("MyCompanyOrName")
QCoreApplication.setOrganizationDomain("mycompany.com") 
QCoreApplication.setApplicationName("MusicAnalyserPlayer")

DARK_THEME_QSS = """QWidget {
    background-color: #1E1E1E;
    color: #D4D4D4;
    font-size: 10pt; 
}

QMainWindow {
    background-color: #1E1E1E;
}

QListWidget {
    background-color: #252526;
    border: 1px solid #333333;
    color: #CCCCCC; 
}

QListWidget::item {
    padding: 5px; 
}

QListWidget::item:selected {
    background-color: #007ACC; 
    color: #FFFFFF; 
}

QListWidget::item:hover {
    background-color: #2A2D2E; 
}

QPushButton {
    background-color: #3C3C3C;
    color: #F0F0F0;
    border: 1px solid #505050;
    padding: 5px 10px;
    min-height: 20px;
}

QPushButton:hover {
    background-color: #4A4A4A;
    border: 1px solid #606060;
}

QPushButton:pressed {
    background-color: #2A2A2A;
}

QPushButton:disabled {
    background-color: #2D2D2D;
    color: #505050;
}

QLabel {
    color: #D4D4D4;
    background-color: transparent; 
}

QLineEdit {
    background-color: #252526;
    border: 1px solid #333333;
    padding: 3px;
    color: #D4D4D4;
}

QSlider::groove:horizontal {
    border: 1px solid #333333;
    height: 8px; 
    background: #303030;
    margin: 2px 0;
}

QSlider::handle:horizontal {
    background: #007ACC;
    border: 1px solid #007ACC;
    width: 18px;
    margin: -2px 0; 
    border-radius: 3px;
}

QTextEdit, QPlainTextEdit { 
    background-color: #252526;
    border: 1px solid #333333;
    color: #D4D4D4;
}

QScrollBar:vertical {
    border: 1px solid #333333;
    background: #252526;
    width: 15px;
    margin: 15px 0 15px 0;
}
QScrollBar::handle:vertical {
    background: #3C3C3C;
    min-height: 20px;
    border-radius: 3px;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    border: 1px solid #333333;
    background: #303030;
    height: 14px;
    subcontrol-position: top;
    subcontrol-origin: margin;
}
QScrollBar::add-line:vertical {
    subcontrol-position: bottom;
}

QScrollBar:horizontal {
    border: 1px solid #333333;
    background: #252526;
    height: 15px;
    margin: 0px 15px 0 15px;
}
QScrollBar::handle:horizontal {
    background: #3C3C3C;
    min-width: 20px;
    border-radius: 3px;
}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    border: 1px solid #333333;
    background: #303030;
    width: 14px;
    subcontrol-position: left;
    subcontrol-origin: margin;
}
QScrollBar::add-line:horizontal {
    subcontrol-position: right;
}

QDialog { 
    background-color: #1E1E1E;
}


QProgressDialog {
    background-color: #252526;
    color: #D4D4D4;
    border: 1px solid #333333;
}
QProgressDialog QLabel {
    color: #D4D4D4;
    background-color: transparent;
}


QMenu {
    background-color: #252526; 
    border: 1px solid #333333; 
    color: #D4D4D4; 
}

QMenu::item {
    padding: 5px 20px 5px 20px; 
}

QMenu::item:selected {
    background-color: #007ACC; 
    color: #FFFFFF; 
}

QMenu::separator {
    height: 1px;
    background: #333333;
    margin-left: 10px;
    margin-right: 5px;
}

"""

def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(DARK_THEME_QSS) 
    
    
    

    main_window = MainWindow()
    main_window.show() 
    sys.exit(app.exec())

if __name__ == '__main__':
    main() 