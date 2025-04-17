from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QLabel, QTabWidget, QPushButton, QListWidget, QHBoxLayout, QMessageBox
from src.core.library import LibraryManager
from src.core.player import PlayerManager
from src.core.analyzer import Analyzer

class MainWindow(QMainWindow):
    def __init__(self, role):
        super().__init__()
        self.role = role
        self.library_manager = LibraryManager()
        self.player_manager = PlayerManager()
        self.analyzer = Analyzer()  # Инициализируем Analyzer
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
        player_layout.addWidget(QLabel("Player Controls"))
        play_button = QPushButton("Play")
        play_button.clicked.connect(self.play_track)
        player_layout.addWidget(play_button)
        pause_button = QPushButton("Pause")
        pause_button.clicked.connect(self.pause_track)
        player_layout.addWidget(pause_button)
        player_tab.setLayout(player_layout)
        tabs.addTab(player_tab, "Player")

        # Вкладка "Analyzer"
        analyzer_tab = QWidget()
        analyzer_layout = QVBoxLayout()
        if self.role == "user":
            analyzer_layout.addWidget(QLabel("Analyzer: Spectrum and Waveform"))
            self.analysis_result = QLabel("Select a track and click Analyze.")
            analyzer_layout.addWidget(self.analysis_result)
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
        selected_item = self.library_list.currentItem()
        if selected_item:
            reply = QMessageBox.question(self, "Delete Track", "Are you sure you want to delete this track?",
                                         QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.Yes:
                track_index = self.library_list.row(selected_item) + 1
                self.library_manager.remove_track(track_index)
                self.library_list.takeItem(self.library_list.row(selected_item))
        else:
            QMessageBox.warning(self, "No Track Selected", "Please select a track to delete.")

    def play_track(self):
        selected_item = self.library_list.currentItem()
        if selected_item:
            track_index = self.library_list.row(selected_item)
            track = self.library_manager.get_tracks()[track_index]
            self.player_manager.set_track(track)
            self.player_manager.play()
        else:
            QMessageBox.warning(self, "No Track Selected", "Please select a track to play.")

    def pause_track(self):
        self.player_manager.pause()

    def analyze_track(self):
        selected_item = self.library_list.currentItem()
        if selected_item:
            track_index = self.library_list.row(selected_item)
            track = self.library_manager.get_tracks()[track_index]
            result = self.analyzer.analyze(track)
            self.analysis_result.setText(result)
        else:
            self.analysis_result.setText("No track selected for analysis!")