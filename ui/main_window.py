import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget,
    QPushButton, QFileDialog, QLabel, QSlider, QListWidget, QListWidgetItem,
    QAbstractItemView, QStyle, QMessageBox, QLineEdit, QProgressDialog, QDialog, QSpinBox, QPushButton,
    QColorDialog, QInputDialog, QMenu
)
from PyQt6.QtMultimedia import QMediaPlayer
from PyQt6.QtCore import QUrl, Qt, QStandardPaths, QTimer, QPoint, QModelIndex, QDir
from PyQt6.QtGui import QColor, QFont, QAction, QKeySequence
import os
import json


from core.lyrics import get_lyrics
from core.player import AudioPlayer
from core.library import MusicLibraryManager, Track 
from core.playlist import PlaylistManager, Playlist 


CONFIG_DIR_NAME = "MusicPlayerApp"
CONFIG_FILE_NAME = "library_config.json" 

class TextSettingsDialog(QDialog):
    def __init__(self, current_font_size, current_text_color, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Text Display Settings")
        layout = QVBoxLayout(self)

        
        font_size_layout = QHBoxLayout()
        font_size_layout.addWidget(QLabel("Font Size:"))
        self.font_size_spinbox = QSpinBox()
        self.font_size_spinbox.setRange(8, 72) 
        self.font_size_spinbox.setValue(current_font_size)
        font_size_layout.addWidget(self.font_size_spinbox)
        layout.addLayout(font_size_layout)

        
        text_color_layout = QHBoxLayout()
        text_color_layout.addWidget(QLabel("Text Color:"))
        self.text_color_button = QPushButton("Choose Color")
        self.current_color = current_text_color
        self._update_color_button_stylesheet(self.current_color)
        self.text_color_button.clicked.connect(self.choose_text_color)
        text_color_layout.addWidget(self.text_color_button)
        layout.addLayout(text_color_layout)

        
        button_box = QHBoxLayout()
        ok_button = QPushButton("OK")
        ok_button.clicked.connect(self.accept)
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        button_box.addWidget(ok_button)
        button_box.addWidget(cancel_button)
        layout.addLayout(button_box)

    def choose_text_color(self):
        color = QColorDialog.getColor(self.current_color, self, "Choose Text Color")
        if color.isValid():
            self.current_color = color
            self._update_color_button_stylesheet(color)
            
    def _update_color_button_stylesheet(self, color):
        self.text_color_button.setStyleSheet(f"background-color: {color.name()};")

    def get_settings(self):
        return self.font_size_spinbox.value(), self.current_color

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Music Analyzer and Player")
        self.setGeometry(100, 100, 1200, 800) 

        
        self.lyrics_font_size = 16
        self.lyrics_text_color = QColor("black")
        self._load_ui_settings() 

        
        self.player = AudioPlayer(self)
        self.library_manager = MusicLibraryManager(self) 
        self.playlist_manager = PlaylistManager(self) 

        
        self.current_track_index_in_playlist = -1
        self.is_playing_playlist = False

        self._setup_ui() 

        
        self.player.mediaStatusChanged.connect(self.handle_media_status_changed)
        self.player.errorOccurred.connect(self.handle_player_error)
        self.player.positionChanged.connect(self.update_lyrics_display)
        self.player.metaDataChanged.connect(self.update_track_info_display)

        
        self.library_manager.libraryUpdated.connect(self.handle_library_scan_finished)
        self.library_manager.libraryLoaded.connect(self.handle_library_loaded) 
        self.library_manager.libraryUpdated.connect(self.update_library_display)
        self.library_manager.scanProgress.connect(self.handle_scan_progress) 

        
        self.playlist_manager.playlistsChanged.connect(self.update_playlist_list_widget)
        self.playlist_manager.playlistsLoaded.connect(self.update_playlist_list_widget) 
        self.playlist_manager.playlistTracksChanged.connect(self.handle_playlist_tracks_changed) 

        self.progress_dialog = None 

        self.show()

        self._current_lyrics = []
        self._current_lyric_index = 0
        self.lyrics_are_synced = False 
        self.current_view_mode = "library" 
        self.current_playlist_id_selected = None

    def _setup_ui(self):
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        
        
        main_splitter_layout = QHBoxLayout(central_widget) 

        
        playlists_panel_layout = QVBoxLayout()
        playlists_panel_layout.addWidget(QLabel("Playlists"))
        
        
        self.view_full_library_button = QPushButton("View Full Library")
        self.view_full_library_button.clicked.connect(self.show_full_library_view)
        playlists_panel_layout.addWidget(self.view_full_library_button)
        
        self.playlist_list_widget = QListWidget()
        self.playlist_list_widget.itemClicked.connect(self.on_playlist_selected)
        self.playlist_list_widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.playlist_list_widget.customContextMenuRequested.connect(self._show_playlist_list_context_menu)
        playlists_panel_layout.addWidget(self.playlist_list_widget)

        playlist_actions_layout = QHBoxLayout()
        create_playlist_button = QPushButton("New Playlist")
        create_playlist_button.clicked.connect(self.create_new_playlist_prompt)
        playlist_actions_layout.addWidget(create_playlist_button)

        playlists_panel_layout.addLayout(playlist_actions_layout)
        main_splitter_layout.addLayout(playlists_panel_layout, 1) 


        
        library_panel_layout = QVBoxLayout()
        library_panel_layout.addWidget(QLabel("Tracks (Library/Playlist)")) 
        
        
        folder_buttons_layout = QHBoxLayout()
        self.add_folder_button = QPushButton("Add Folder to Library")
        self.add_folder_button.clicked.connect(self.add_music_folder_to_library)
        folder_buttons_layout.addWidget(self.add_folder_button)

        self.rescan_button = QPushButton("Rescan Library")
        self.rescan_button.clicked.connect(self.rescan_all_folders_in_library)
        folder_buttons_layout.addWidget(self.rescan_button)
        library_panel_layout.addLayout(folder_buttons_layout)

        self.track_search_input = QLineEdit() 
        self.track_search_input.setPlaceholderText("Search tracks...")
        self.track_search_input.textChanged.connect(self.filter_track_list_display)
        library_panel_layout.addWidget(self.track_search_input)

        self.track_list_widget = QListWidget() 
        self.track_list_widget.itemDoubleClicked.connect(self.play_selected_from_track_list)
        self.track_list_widget.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        self.track_list_widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.track_list_widget.customContextMenuRequested.connect(self._show_track_list_context_menu)
        
        
        self.track_list_widget.setDragEnabled(True)
        self.track_list_widget.setAcceptDrops(True)
        self.track_list_widget.setDropIndicatorShown(True)
        
        self.track_list_widget.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        
        self.track_list_widget.model().rowsMoved.connect(self._handle_track_reorder_in_playlist)

        library_panel_layout.addWidget(self.track_list_widget)

        self.remove_tracks_button = QPushButton("Remove Selected Tracks") 
        self.remove_tracks_button.clicked.connect(self.remove_selected_tracks_from_current_view)
        library_panel_layout.addWidget(self.remove_tracks_button)
        main_splitter_layout.addLayout(library_panel_layout, 2) 
        
        
        player_lyrics_layout = QVBoxLayout()
        
        self.open_button = QPushButton("Open Single File")
        self.open_button.clicked.connect(self.open_single_file)
        player_lyrics_layout.addWidget(self.open_button)

        self.play_button = QPushButton("Play")
        self.play_icon = self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPlay) 
        self.pause_icon = self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPause)
        self.play_button.setIcon(self.play_icon)
        self.play_button.clicked.connect(self.toggle_play_pause)
        self.play_button.setEnabled(False)
        player_lyrics_layout.addWidget(self.play_button)

        self.current_track_label = QLabel("No track loaded.")
        self.current_track_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        player_lyrics_layout.addWidget(self.current_track_label)

        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(self.player.get_volume()) 
        self.volume_slider.valueChanged.connect(self.player.set_volume) 
        
        volume_layout = QHBoxLayout()
        volume_layout.addWidget(QLabel("Volume:"))
        volume_layout.addWidget(self.volume_slider)
        player_lyrics_layout.addLayout(volume_layout)

        self.text_settings_button = QPushButton("Text Settings")
        self.text_settings_button.clicked.connect(self.open_text_settings_dialog)
        player_lyrics_layout.addWidget(self.text_settings_button)

        self.lyrics_label = QLabel("Lyrics will appear here...")
        self.lyrics_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._apply_lyrics_style()
        player_lyrics_layout.addWidget(self.lyrics_label, 1)
        main_splitter_layout.addLayout(player_lyrics_layout, 2) 

    def _show_track_list_context_menu(self, position: QPoint):
        selected_items = self.track_list_widget.selectedItems()
        if not selected_items: 
            return

        context_menu = QMenu(self)
        
        add_to_playlist_menu = context_menu.addMenu("Add Selected to Playlist")
        all_playlists = self.playlist_manager.get_all_playlists()

        if not all_playlists:
            no_playlists_action = QAction("No playlists available", self)
            no_playlists_action.setEnabled(False)
            add_to_playlist_menu.addAction(no_playlists_action)
        else:
            for pl in all_playlists:
                playlist_action = QAction(pl.name, self)
                playlist_action.triggered.connect(lambda checked=False, p_id=pl.id: self._add_selected_tracks_to_playlist(p_id))
                add_to_playlist_menu.addAction(playlist_action)

        context_menu.exec(self.track_list_widget.mapToGlobal(position))

    def _add_selected_tracks_to_playlist(self, playlist_id):
        selected_items = self.track_list_widget.selectedItems()
        if not selected_items:
            QMessageBox.information(self, "Information", "No tracks selected.")
            return

        playlist = self.playlist_manager.get_playlist_by_id(playlist_id)
        if not playlist:
            QMessageBox.warning(self, "Error", "Selected playlist not found.")
            return
        
        added_count = 0
        for item in selected_items:
            file_path = item.data(Qt.ItemDataRole.UserRole) 
            if self.playlist_manager.add_track_to_playlist(playlist_id, file_path):
                added_count += 1
        
        if added_count > 0:
            QMessageBox.information(self, "Success", f"{added_count} track(s) added to '{playlist.name}'.")
        else:
            QMessageBox.information(self, "Information", f"No new tracks added to '{playlist.name}'. They might already be in the playlist.")

    def handle_playlist_tracks_changed(self, playlist_id_changed):
        
        if self.current_view_mode == "playlist" and self.current_playlist_id_selected == playlist_id_changed:
            self.update_track_list_for_playlist(playlist_id_changed)

    def handle_library_loaded(self):
        print("DEBUG: MainWindow received libraryLoaded signal.")
        self.update_library_display()
        self.update_playlist_list_widget()

    def add_music_folder_to_library(self):
        folder_path = QFileDialog.getExistingDirectory(self, "Select Music Folder")
        if folder_path:
            if self.library_manager.add_library_folder(folder_path):
                self.library_manager.save_library_to_disk() 
                self.rescan_all_folders_in_library() 
            else:
                 QMessageBox.information(self, "Folder Not Added", "The selected folder could not be added or is already in the library path list.")

    def rescan_all_folders_in_library(self):
        if not self.library_manager.get_library_folders():
            QMessageBox.information(self, "No Library Folders", "Please add a music folder to the library first.")
            return

        if self.progress_dialog and self.progress_dialog.isVisible():
            self.progress_dialog.cancel() 

        self.progress_dialog = QProgressDialog("Scanning library...", "Cancel", 0, 0, self)
        self.progress_dialog.setWindowTitle("Library Scan")
        self.progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
        self.progress_dialog.setAutoClose(True)
        self.progress_dialog.setAutoReset(True)
        self.progress_dialog.canceled.connect(self._cancel_scan_progress) 
        self.progress_dialog.setValue(0) 
        self.progress_dialog.show()
        
        
        QTimer.singleShot(100, self.library_manager.scan_all_library_folders)

    def _cancel_scan_progress(self):
        
        
        if self.progress_dialog:
            self.progress_dialog.hide()
        print("DEBUG: Library scan cancel requested by user.")

    def handle_scan_progress(self, files_scanned, current_file):
        if self.progress_dialog:
            self.progress_dialog.setLabelText(f"Scanning: {os.path.basename(current_file)}")
            self.progress_dialog.setValue(files_scanned % self.progress_dialog.maximum() if self.progress_dialog.maximum() > 0 else files_scanned)

    def handle_library_scan_finished(self, new_tracks_data):
        if self.progress_dialog:
            self.progress_dialog.hide()
        
        num_new_tracks = len(new_tracks_data)
        QMessageBox.information(self, "Scan Complete", f"Library scan finished. Added {num_new_tracks} new track(s).")
        
        if self.current_view_mode == "library":
            self.update_library_display()
        
        self.library_manager.save_library_to_disk()

    def update_library_display(self): 
        print("DEBUG: update_library_display called (full library view)")
        self.track_list_widget.clear()
        tracks_data = self.library_manager.get_all_tracks_for_ui_update()
        for track_info in tracks_data:
            item = QListWidgetItem(track_info['text'])
            item.setData(Qt.ItemDataRole.UserRole, track_info['file_path']) 
            self.track_list_widget.addItem(item)
        
        self.current_track_label.setText("Select a track from the library.")
        self.play_button.setEnabled(False)
        self._update_play_pause_button_state()
        self.filter_track_list_display() 

    def filter_track_list_display(self):
        search_text = self.track_search_input.text().lower()
        for i in range(self.track_list_widget.count()):
            item = self.track_list_widget.item(i)
            item_text = item.text().lower()
            
            if search_text in item_text:
                item.setHidden(False)
            else:
                item.setHidden(True)

    def _play_audio_file(self, file_path, playlist_track_index=None):
        print(f"DEBUG: _play_audio_file called with: {file_path}, playlist_track_index: {playlist_track_index}")
        if not os.path.exists(file_path):
            QMessageBox.warning(self, "File Not Found", f"The audio file could not be found:\n{file_path}")
            
            if self.current_view_mode == "library":
                self.library_manager.remove_track_by_path(file_path)
                self.update_library_display() 
            elif self.current_view_mode == "playlist" and self.current_playlist_id_selected:
                self.playlist_manager.remove_track_from_playlist(self.current_playlist_id_selected, file_path)
                
            self.player.stop()
            self.play_button.setEnabled(False)
            self.current_track_label.setText("Error: Track not found.")
            self._update_play_pause_button_state()
            return

        print(f"DEBUG: Setting player source to: {file_path}")
        self.player.set_source(file_path)
        print(f"DEBUG: Player source set. Attempting to play...")
        self.player.play()
        print(f"DEBUG: self.player.play() called.")
        self.play_button.setEnabled(True)
        self._update_play_pause_button_state()

        track = self.library_manager.get_track_by_path(file_path) 
        if track:
            self.current_track_label.setText(f"Now Playing: {track.title} - {track.artist}")
            self.load_lyrics(track.file_path)
            # print(f"DEBUG: Temporarily skipped load_lyrics for {track.file_path}")
        else:
            
            self.current_track_label.setText(f"Now Playing: {os.path.basename(file_path)}")
            self.load_lyrics(file_path)
            # print(f"DEBUG: Temporarily skipped load_lyrics for {file_path} (track not in library_manager)")

        if playlist_track_index is not None:
            self.is_playing_playlist = True
            self.current_track_index_in_playlist = playlist_track_index
            print(f"DEBUG: Set is_playing_playlist=True, current_track_index_in_playlist={self.current_track_index_in_playlist}")
        else:
            self.is_playing_playlist = False
            self.current_track_index_in_playlist = -1
            print(f"DEBUG: Set is_playing_playlist=False, current_track_index_in_playlist cleared")

    def play_selected_from_track_list(self, item):
        file_path = item.data(Qt.ItemDataRole.UserRole)
        current_row = self.track_list_widget.row(item)

        if self.current_view_mode == "playlist":
            self._play_audio_file(file_path, playlist_track_index=current_row)
        else:
            self._play_audio_file(file_path) 

    def open_single_file(self): 
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open Audio File",
            QStandardPaths.standardLocations(QStandardPaths.StandardLocation.MusicLocation)[0],
            "Audio Files (*.mp3 *.wav *.flac *.aac *.m4a *.ogg);;All Files (*)"
        )
        print(f"DEBUG: open_single_file selected: {file_path}")
        if file_path:
            self._play_audio_file(file_path)
            self.current_view_mode = "library" 
            if self.playlist_list_widget.currentItem():
                 self.playlist_list_widget.currentItem().setSelected(False)
            self.current_playlist_id_selected = None
            self.update_library_display() 

    def load_lyrics(self, audio_file_path):
        print(f"DEBUG: Calling load_lyrics for: {audio_file_path}")
        self._current_lyrics = []
        self._current_lyric_index = -1 
        self.lyrics_label.setText("Loading lyrics...")

        lyrics_data, is_synced = get_lyrics(audio_file_path)
        self.lyrics_are_synced = is_synced

        print(f"DEBUG: load_lyrics result: {len(lyrics_data)} lines, is_synced: {is_synced}")

        if lyrics_data:
            self._current_lyrics = lyrics_data
            if self.lyrics_are_synced:
                self.lyrics_label.setText("Lyrics loaded. Play to sync.") 
                self.update_lyrics_display(0) 
            else:
                
                full_text = "\n".join([line[1] for line in lyrics_data])
                self.lyrics_label.setText(full_text)
        else:
            self.lyrics_label.setText("No lyrics found for this track.")

    def toggle_play_pause(self):
        print(f"DEBUG: toggle_play_pause called. Current state: {self.player.playback_state()}")
        if self.player.playback_state() == QMediaPlayer.PlaybackState.PlayingState:
            self.player.pause()
        elif self.player.playback_state() == QMediaPlayer.PlaybackState.PausedState or \
             self.player.playback_state() == QMediaPlayer.PlaybackState.StoppedState:
            
            if self.player.source_url().isEmpty() and self.track_list_widget.count() > 0:
                first_item = self.track_list_widget.item(0)
                if first_item:
                    self.play_selected_from_track_list(first_item)
                else:
                    self.player.play()
            else:
                self.player.play()
        self._update_play_pause_button_state()

    def _update_play_pause_button_state(self):
        if self.player.playback_state() == QMediaPlayer.PlaybackState.PlayingState:
            self.play_button.setIcon(self.pause_icon)
            self.play_button.setText("Pause")
        else:
            self.play_button.setIcon(self.play_icon)
            self.play_button.setText("Play")

    def update_lyrics_display(self, position_ms):
        if not self._current_lyrics or not self.lyrics_are_synced:
            if not self.lyrics_are_synced and self._current_lyrics and isinstance(self._current_lyrics[0][1], str):
                pass 
            return

        new_lyric_index = -1
        for i, (timestamp, line) in enumerate(self._current_lyrics):
            if position_ms >= timestamp:
                new_lyric_index = i
            else:
                break
        
        if new_lyric_index != self._current_lyric_index and new_lyric_index != -1:
            self._current_lyric_index = new_lyric_index
            current_line_text = self._current_lyrics[self._current_lyric_index][1]
            
            
            display_text = ""
            context_lines = 2 

            start_index = max(0, self._current_lyric_index - context_lines)
            end_index = min(len(self._current_lyrics), self._current_lyric_index + context_lines + 1)

            for i in range(start_index, end_index):
                line_ts, line_txt = self._current_lyrics[i]
                if i == self._current_lyric_index:
                    display_text += f"<b>{line_txt}</b>\n"
                else:
                    display_text += f"<span style='color:grey;'>{line_txt}</span>\n"
            
            self.lyrics_label.setText(display_text.strip())
        elif new_lyric_index == -1 and self._current_lyrics: 
            self.lyrics_label.setText("<span style='color:grey;'>" + self._current_lyrics[0][1] + "</span>")

    def update_track_info_display(self):
        print("DEBUG: update_track_info_display called (STABLE VERSION - NO METADATA FETCH FROM PLAYER)")
        try:
            if self.player.current_source_path:
                # Display filename as a fallback since fetching metadata is unstable
                base_name = os.path.basename(self.player.current_source_path)
                track_display_name = os.path.splitext(base_name)[0]
                self.current_track_label.setText(f"Now Playing: {track_display_name}")
                print(f"DEBUG: Displaying filename as track info: {track_display_name}")
            else:
                self.current_track_label.setText("No track loaded.")
                print("DEBUG: No current source path, track label set to 'No track loaded'.")
            
            # All problematic QMediaPlayer metadata/duration calls are removed here.
            # The Track object creation part is also removed as it relied on that metadata.
            # If a track object is needed here for other reasons in the future, 
            # it should rely on library_manager.get_track_by_path or similar.

        except BaseException as e: 
            print(f"CRITICAL_ERROR in update_track_info_display (STABLE VERSION): {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            try:
                self.current_track_label.setText("Error updating track info.")
            except Exception as e_label:
                print(f"CRITICAL_ERROR: Could not even set error label: {e_label}")

    def remove_selected_tracks_from_current_view(self):
        selected_items = self.track_list_widget.selectedItems()
        if not selected_items:
            QMessageBox.information(self, "Nothing Selected", "Please select tracks to remove.")
            return

        confirm_msg = f"Are you sure you want to remove {len(selected_items)} selected track(s)?\n"
        if self.current_view_mode == "library":
            confirm_msg += "This will remove them from the library view but not delete files from disk."
        elif self.current_view_mode == "playlist":
            playlist = self.playlist_manager.get_playlist_by_id(self.current_playlist_id_selected)
            playlist_name = playlist.name if playlist else "the current playlist"
            confirm_msg += f"This will remove them from '{playlist_name}' but not from the main library or disk."
        else:
            return 

        reply = QMessageBox.question(self, 'Confirm Removal', confirm_msg, 
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, 
                                     QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            for item in selected_items:
                file_path = item.data(Qt.ItemDataRole.UserRole)
                row = self.track_list_widget.row(item)

                if self.current_view_mode == "library":
                    self.library_manager.remove_track_by_path(file_path)
                elif self.current_view_mode == "playlist" and self.current_playlist_id_selected:
                    self.playlist_manager.remove_track_from_playlist(self.current_playlist_id_selected, file_path)
                
                self.track_list_widget.takeItem(row)
            
            if self.current_view_mode == "library":
                self.library_manager.save_library_to_disk() 
            elif self.current_view_mode == "playlist":
                self.playlist_manager.save_playlists_to_disk()
                

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Delete:
            if self.track_list_widget.hasFocus() and self.track_list_widget.selectedItems():
                self.remove_selected_tracks_from_current_view()
            elif self.playlist_list_widget.hasFocus() and self.playlist_list_widget.currentItem():
                current_pl_item = self.playlist_list_widget.currentItem()
                playlist_id = current_pl_item.data(Qt.ItemDataRole.UserRole)
                playlist = self.playlist_manager.get_playlist_by_id(playlist_id)
                if playlist:
                    self.delete_selected_playlist_prompt(playlist_id, playlist.name)
        elif event.key() == Qt.Key.Key_F2:
            if self.playlist_list_widget.hasFocus() and self.playlist_list_widget.currentItem():
                current_pl_item = self.playlist_list_widget.currentItem()
                playlist_id = current_pl_item.data(Qt.ItemDataRole.UserRole)
                playlist = self.playlist_manager.get_playlist_by_id(playlist_id)
                if playlist:
                    self.rename_selected_playlist_prompt(playlist_id, playlist.name)
        else:
            super().keyPressEvent(event)

    def handle_media_status_changed(self, status):
        print(f"DEBUG: handle_media_status_changed: {status}")
        if status == QMediaPlayer.MediaStatus.LoadedMedia:
            self.play_button.setEnabled(True)
            self.update_track_info_display()
        elif status == QMediaPlayer.MediaStatus.EndOfMedia:
            print("DEBUG: EndOfMedia status received.")
            self.current_track_label.setText(f"{self.current_track_label.text()} (Finished)")
            self._update_play_pause_button_state()
            
            if self.is_playing_playlist and self.current_playlist_id_selected:
                print(f"DEBUG: is_playing_playlist is True. Current index: {self.current_track_index_in_playlist}")
                playlist = self.playlist_manager.get_playlist_by_id(self.current_playlist_id_selected)
                if playlist and self.current_track_index_in_playlist < len(playlist.track_paths) - 1:
                    self.current_track_index_in_playlist += 1
                    next_track_path = playlist.track_paths[self.current_track_index_in_playlist]
                    print(f"DEBUG: Playing next track in playlist: {next_track_path} at index {self.current_track_index_in_playlist}")
                    self._play_audio_file(next_track_path, playlist_track_index=self.current_track_index_in_playlist)
                    
                    
                    list_widget_item = self.track_list_widget.item(self.current_track_index_in_playlist)
                    if list_widget_item:
                        self.track_list_widget.setCurrentItem(list_widget_item)
                else:
                    print("DEBUG: Reached end of playlist or playlist is empty/invalid.")
                    self.is_playing_playlist = False
                    self.current_track_index_in_playlist = -1
                    self.player.stop() 
                    self._update_play_pause_button_state()
            else:
                print("DEBUG: Not playing a playlist or no playlist selected. Stopping.")
                self.is_playing_playlist = False 
                self.current_track_index_in_playlist = -1
                self.player.stop()
                self._update_play_pause_button_state()

        elif status == QMediaPlayer.MediaStatus.InvalidMedia:
            QMessageBox.critical(self, "Error", "Invalid media. Cannot play this file.")
            self.play_button.setEnabled(False)
            self.current_track_label.setText("Error: Invalid Media")
            self.lyrics_label.setText("Lyrics not available.")
            self._current_lyrics = []
            self.is_playing_playlist = False 
            self.current_track_index_in_playlist = -1 
            self._update_play_pause_button_state()
        elif status == QMediaPlayer.MediaStatus.NoMedia:
            self.play_button.setEnabled(False)
            self.current_track_label.setText("No track loaded.")
            self.lyrics_label.setText("Lyrics will appear here...")
            self._current_lyrics = []
            self.is_playing_playlist = False 
            self.current_track_index_in_playlist = -1             
            self._update_play_pause_button_state()

    def handle_player_error(self, error_enum, error_string):
        print(f"DEBUG Player Error: Enum {error_enum}, String: {error_string}") 
        QMessageBox.critical(self, "Player Error", f"An error occurred: {error_string}")
        self.play_button.setEnabled(False)
        self._update_play_pause_button_state()

    def closeEvent(self, event):
        self.library_manager.save_library_to_disk()
        self.playlist_manager.save_playlists_to_disk()
        self._save_ui_settings()
        super().closeEvent(event)

    def _apply_lyrics_style(self):
        
        
        
        font = QFont()
        font.setPointSize(self.lyrics_font_size)
        self.lyrics_label.setFont(font)
        
        
        text_color_name = self.lyrics_text_color.name()
        self.lyrics_label.setStyleSheet(f"color: {text_color_name}; background-color: transparent; border: 1px solid #333333; padding: 5px;")

    def open_text_settings_dialog(self):
        dialog = TextSettingsDialog(self.lyrics_font_size, self.lyrics_text_color, self)
        if dialog.exec():
            self.lyrics_font_size, self.lyrics_text_color = dialog.get_settings()
            self._apply_lyrics_style()
            self._save_ui_settings() 

    def _get_config_file_path(self): 
        config_dir_path = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppConfigLocation)
        if not config_dir_path:
            config_dir_path = os.path.join(os.path.expanduser("~"), "MusicPlayerApp") 
        
        app_config_dir = QDir(os.path.join(config_dir_path, CONFIG_DIR_NAME))
        if not app_config_dir.exists():
            app_config_dir.mkpath(".")
        return os.path.join(app_config_dir.absolutePath(), CONFIG_FILE_NAME)

    def _save_ui_settings(self):
        config_path = self._get_config_file_path()
        try:
            all_config_data = {}
            if os.path.exists(config_path):
                try:
                    with open(config_path, 'r', encoding='utf-8') as f:
                        all_config_data = json.load(f)
                except json.JSONDecodeError:
                    print(f"Warning: Config file {config_path} corrupted. UI settings will create/overwrite their section.")
            
            all_config_data["ui_settings"] = {
                "lyrics_font_size": self.lyrics_font_size,
                "lyrics_text_color": self.lyrics_text_color.name() 
            }
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(all_config_data, f, indent=4)
            print(f"UI settings saved to {config_path}")
        except IOError as e:
            print(f"Error saving UI settings: {e}")

    def _load_ui_settings(self):
        config_path = self._get_config_file_path()
        if not os.path.exists(config_path):
            print("UI settings file not found. Using defaults.")
            return
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                all_config_data = json.load(f)
            ui_settings = all_config_data.get("ui_settings")
            if ui_settings:
                self.lyrics_font_size = ui_settings.get("lyrics_font_size", 16)
                color_name = ui_settings.get("lyrics_text_color", "#000000") 
                self.lyrics_text_color = QColor(color_name)
                print(f"UI settings loaded: Font Size={self.lyrics_font_size}, Color={self.lyrics_text_color.name()}")
            else:
                print("No UI settings found in config file. Using defaults.")
        except (IOError, json.JSONDecodeError) as e:
            print(f"Error loading UI settings: {e}. Using defaults.")
        finally:
            if hasattr(self, 'lyrics_label'): 
                self._apply_lyrics_style()

    def update_playlist_list_widget(self):
        self.playlist_list_widget.clear()
        playlists = self.playlist_manager.get_all_playlists()
        for pl in playlists:
            item = QListWidgetItem(pl.name)
            item.setData(Qt.ItemDataRole.UserRole, pl.id) 
            self.playlist_list_widget.addItem(item)
            
            if pl.id == self.current_playlist_id_selected:
                self.playlist_list_widget.setCurrentItem(item)
        print(f"DEBUG: Playlist list widget updated. {len(playlists)} playlists loaded.")

    def create_new_playlist_prompt(self):
        name, ok = QInputDialog.getText(self, "New Playlist", "Enter playlist name:")
        if ok and name.strip():
            new_playlist = self.playlist_manager.create_playlist(name.strip())
            if new_playlist:
                self.playlist_manager.save_playlists_to_disk() 
                
                for i in range(self.playlist_list_widget.count()):
                    if self.playlist_list_widget.item(i).data(Qt.ItemDataRole.UserRole) == new_playlist.id:
                        self.playlist_list_widget.setCurrentRow(i)
                        break
            else:
                QMessageBox.warning(self, "Error", "Could not create playlist. Name might be empty or already exist.")
        elif ok and not name.strip():
            QMessageBox.warning(self, "Invalid Name", "Playlist name cannot be empty.")

    def on_playlist_selected(self, item):
        if not item: 
            self.show_full_library_view()
            return

        playlist_id = item.data(Qt.ItemDataRole.UserRole)
        print(f"DEBUG: on_playlist_selected: ID={playlist_id}, Name='{item.text()}'")
        
        if self.current_playlist_id_selected == playlist_id and self.current_view_mode == "playlist":
            print("DEBUG: Same playlist selected again. No change in view.")
            return

        self.current_playlist_id_selected = playlist_id
        self.current_view_mode = "playlist"
        self.update_track_list_for_playlist(playlist_id)
        
        
        self.is_playing_playlist = False
        self.current_track_index_in_playlist = -1
        
        if self.player.playback_state() != QMediaPlayer.PlaybackState.StoppedState:
            current_playing_file = self.player.source_url().toLocalFile()
            playlist = self.playlist_manager.get_playlist_by_id(playlist_id)
            if playlist and current_playing_file in playlist.track_paths:
                
                self.is_playing_playlist = True
                try:
                    self.current_track_index_in_playlist = playlist.track_paths.index(current_playing_file)
                except ValueError:
                    self.current_track_index_in_playlist = -1 
                    self.is_playing_playlist = False 
            else:
                pass 
                

    def update_track_list_for_playlist(self, playlist_id):
        self.track_list_widget.clear()
        playlist = self.playlist_manager.get_playlist_by_id(playlist_id)
        if playlist:
            print(f"DEBUG: Updating track list for playlist '{playlist.name}'. Tracks: {len(playlist.track_paths)}")
            for track_path in playlist.track_paths:
                track_obj = self.library_manager.get_track_by_path(track_path)
                if track_obj:
                    display_text = f"{track_obj.title} - {track_obj.artist} ({track_obj.album})"
                    item = QListWidgetItem(display_text)
                    item.setData(Qt.ItemDataRole.UserRole, track_path)
                    self.track_list_widget.addItem(item)
                else:
                    item = QListWidgetItem(f"[Missing Track] {os.path.basename(track_path)}")
                    item.setData(Qt.ItemDataRole.UserRole, track_path)
                    item.setForeground(QColor("grey")) 
                    self.track_list_widget.addItem(item)
            
            self.current_track_label.setText(f"Viewing Playlist: {playlist.name}")
        else:
            print(f"DEBUG: Playlist ID {playlist_id} not found when updating track list.")
            self.current_track_label.setText("Playlist not found.")
        self.filter_track_list_display() 

    def _show_playlist_list_context_menu(self, position: QPoint):
        item = self.playlist_list_widget.itemAt(position)
        if not item:
            return

        playlist_id = item.data(Qt.ItemDataRole.UserRole)
        playlist = self.playlist_manager.get_playlist_by_id(playlist_id)
        if not playlist: return

        context_menu = QMenu(self)
        rename_action = QAction("Rename Playlist", self)
        rename_action.triggered.connect(lambda: self.rename_selected_playlist_prompt(playlist_id, playlist.name))
        context_menu.addAction(rename_action)

        delete_action = QAction("Delete Playlist", self)
        delete_action.triggered.connect(lambda: self.delete_selected_playlist_prompt(playlist_id, playlist.name))
        context_menu.addAction(delete_action)
        
        context_menu.exec(self.playlist_list_widget.mapToGlobal(position))

    def rename_selected_playlist_prompt(self, playlist_id, current_name):
        new_name, ok = QInputDialog.getText(self, "Rename Playlist", "Enter new name:", QLineEdit.EchoMode.Normal, current_name)
        if ok and new_name.strip():
            if self.playlist_manager.rename_playlist(playlist_id, new_name.strip()):
                self.playlist_manager.save_playlists_to_disk()
                
            else:
                QMessageBox.warning(self, "Error", "Could not rename playlist. Name might be empty or already exist.")
        elif ok and not new_name.strip():
            QMessageBox.warning(self, "Invalid Name", "Playlist name cannot be empty.")

    def delete_selected_playlist_prompt(self, playlist_id, playlist_name):
        reply = QMessageBox.question(self, 'Confirm Delete', 
                                     f"Are you sure you want to delete the playlist '{playlist_name}'?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, 
                                     QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            if self.playlist_manager.delete_playlist(playlist_id):
                self.playlist_manager.save_playlists_to_disk() 
                
                if self.current_playlist_id_selected == playlist_id:
                    
                    self.player.stop()
                    self.is_playing_playlist = False
                    self.current_track_index_in_playlist = -1
                    self.current_playlist_id_selected = None 
                    self._update_play_pause_button_state()
                    self.show_full_library_view()
                
                
            else:
                QMessageBox.warning(self, "Error", "Could not delete playlist.")

    def show_full_library_view(self):
        print("DEBUG: Switched to full library view.")
        self.current_view_mode = "library"
        self.current_playlist_id_selected = None
        if self.playlist_list_widget.currentItem():
            self.playlist_list_widget.currentItem().setSelected(False) 
            self.playlist_list_widget.clearSelection()
        
        self.update_library_display()
        
        self.is_playing_playlist = False
        self.current_track_index_in_playlist = -1
        
        
        
        self.track_list_widget.setDragDropMode(QAbstractItemView.DragDropMode.NoDragDrop) 

    def _handle_track_reorder_in_playlist(self, source_parent: QModelIndex, source_start: int, source_end: int, destination_parent: QModelIndex, destination_row: int):
        
        
        if self.current_view_mode != "playlist" or not self.current_playlist_id_selected:
            print("DEBUG: Track reorder ignored, not in playlist view.")
            return
        
        print(f"DEBUG: _handle_track_reorder_in_playlist: src_parent={source_parent.row()}, src_start={source_start}, src_end={source_end}, dst_parent={destination_parent.row()}, dst_row={destination_row}")

        
        if source_parent != destination_parent:
            print("DEBUG: Track reorder ignored, cross-model move detected (should not happen with InternalMove).")
            return

        new_ordered_paths = []
        for i in range(self.track_list_widget.count()):
            item = self.track_list_widget.item(i)
            new_ordered_paths.append(item.data(Qt.ItemDataRole.UserRole))
        
        print(f"DEBUG: New ordered paths for playlist {self.current_playlist_id_selected}: {new_ordered_paths}")

        current_playing_path_before_reorder = None
        if self.is_playing_playlist and self.current_track_index_in_playlist != -1:
            playlist_obj = self.playlist_manager.get_playlist_by_id(self.current_playlist_id_selected)
            if playlist_obj and 0 <= self.current_track_index_in_playlist < len(playlist_obj.track_paths):
                 current_playing_path_before_reorder = playlist_obj.track_paths[self.current_track_index_in_playlist]

        if self.playlist_manager.reorder_tracks_in_playlist(self.current_playlist_id_selected, new_ordered_paths):
            self.playlist_manager.save_playlists_to_disk() 
            print(f"DEBUG: Successfully reordered tracks for playlist {self.current_playlist_id_selected} in manager.")

            
            if current_playing_path_before_reorder:
                try:
                    self.current_track_index_in_playlist = new_ordered_paths.index(current_playing_path_before_reorder)
                    print(f"DEBUG: Updated current_track_index_in_playlist to {self.current_track_index_in_playlist} after reorder.")
                except ValueError:
                    print(f"DEBUG: Playing track {current_playing_path_before_reorder} not found in new order. Resetting index.")
                    self.current_track_index_in_playlist = -1 
                    self.is_playing_playlist = False 
        else:
            print(f"DEBUG: Failed to reorder tracks for playlist {self.current_playlist_id_selected} in manager. UI might be out of sync.")
            
            QMessageBox.warning(self, "Reorder Failed", "Could not save the new track order. Please try again.")
            self.update_track_list_for_playlist(self.current_playlist_id_selected)


