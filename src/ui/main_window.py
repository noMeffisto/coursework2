from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QLabel, QTabWidget, QPushButton, QListWidget, QHBoxLayout
from src.core.library import LibraryManager

class MainWindow(QMainWindow):
    def __init__(self, role):
        super().__init__()
        self.role = role
        self.library_manager = LibraryManager()
        self.setWindowTitle("Music Analyzer")
        self.setMinimumSize(800, 600)
        self.init_ui()

    def init_ui(self):
        central_widget = QWidget()
        layout = QVBoxLayout()
        central_widget.setLayout(layout)

        tabs = QTabWidget()
        layout.addWidget(tabs)

        # Вкладка "Library"
        library_tab = QWidget()
        library_layout = QVBoxLayout()
        self.library_list = QListWidget()
        for track in self.library_manager.get_tracks():
            self.library_list.addItem(f"{track['title']} - {track['artist']}")
        library_layout.addWidget(self.library_list)

        if self.role == "user":
            # Создаём горизонтальный layout для кнопок
            button_layout = QHBoxLayout()
            add_track_button = QPushButton("Add Track")
            add_track_button.clicked.connect(self.add_track)
            button_layout.addWidget(add_track_button)

            delete_track_button = QPushButton("Delete Track")
            delete_track_button.clicked.connect(self.delete_track)
            button_layout.addWidget(delete_track_button)

            library_layout.addLayout(button_layout)

        library_tab.setLayout(library_layout)
        tabs.addTab(library_tab, "Library")

        # Вкладка "Player"
        player_tab = QWidget()
        player_layout = QVBoxLayout()
        player_layout.addWidget(QLabel("Player Controls (Play/Pause)"))
        play_button = QPushButton("Play")
        play_button.clicked.connect(self.play_track)
        player_layout.addWidget(play_button)
        player_tab.setLayout(player_layout)
        tabs.addTab(player_tab, "Player")

        # Вкладка "Analyzer"
        analyzer_tab = QWidget()
        analyzer_layout = QVBoxLayout()
        if self.role == "user":
            analyzer_layout.addWidget(QLabel("Analyzer: Spectrum and Waveform (Placeholder)"))
            analyze_button = QPushButton("Analyze")
            analyze_button.clicked.connect(self.analyze_track)
            analyzer_layout.addWidget(analyze_button)
        else:
            analyzer_layout.addWidget(QLabel("Analysis is not available for Guest"))
        analyzer_tab.setLayout(analyzer_layout)
        tabs.addTab(analyzer_tab, "Analyzer")

        self.setCentralWidget(central_widget)

    def add_track(self):
        new_track = {"id": len(self.library_manager.get_tracks()) + 1, "title": "New Song", "artist": "New Artist", "duration": 150}
        self.library_manager.add_track(new_track)
        self.library_list.addItem(f"{new_track['title']} - {new_track['artist']}")

    def delete_track(self):
        selected_item = self.library_list.currentItem()  # Получаем выбранный элемент
        if selected_item:
            # Извлекаем ID трека из текста (предполагаем, что ID совпадает с индексом + 1)
            track_text = selected_item.text()
            track_index = self.library_list.row(selected_item) + 1  # ID трека
            self.library_manager.remove_track(track_index)  # Удаляем трек из LibraryManager
            self.library_list.takeItem(self.library_list.row(selected_item))  # Удаляем из списка в UI

    def play_track(self):
        print("Playing track (placeholder)")

    def analyze_track(self):
        print("Analyzing track (placeholder)")