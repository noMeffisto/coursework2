import os
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput, QMediaMetaData
from PyQt6.QtCore import QObject, pyqtSignal, QUrl, QStandardPaths

class AudioPlayer(QObject):
    # Signals to communicate with MainWindow or other UI components
    mediaStatusChanged = pyqtSignal(QMediaPlayer.MediaStatus)
    playbackStateChanged = pyqtSignal(QMediaPlayer.PlaybackState)
    errorOccurred = pyqtSignal(QMediaPlayer.Error, str)
    positionChanged = pyqtSignal(int)  # position in milliseconds
    metaDataChanged = pyqtSignal() # For track info updates
    durationChanged = pyqtSignal(int) # duration in milliseconds

    def __init__(self, parent=None):
        super().__init__(parent)
        self._player = QMediaPlayer()
        self._audio_output = QAudioOutput()
        self._player.setAudioOutput(self._audio_output)

        # Connect internal QMediaPlayer signals to our custom signals
        self._player.mediaStatusChanged.connect(self.mediaStatusChanged.emit)
        self._player.playbackStateChanged.connect(self.playbackStateChanged.emit)
        self._player.errorOccurred.connect(self._handle_error) # Use a handler to pass error string
        self._player.positionChanged.connect(self.positionChanged.emit)
        self._player.metaDataChanged.connect(self.metaDataChanged.emit)
        self._player.durationChanged.connect(self.durationChanged.emit)

        self.current_source_path = None

    def _handle_error(self, error):
        # QMediaPlayer.errorOccurred only gives the enum, we need the string too.
        self.errorOccurred.emit(error, self._player.errorString())

    def set_source(self, file_path):
        if file_path:
            self.current_source_path = file_path
            self._player.setSource(QUrl.fromLocalFile(file_path))
        else:
            self.current_source_path = None
            self._player.setSource(QUrl())

    def play(self):
        print("PLAYER_DEBUG: AudioPlayer.play() called.")
        if self.current_source_path:
            print(f"PLAYER_DEBUG: Current source path is set: {self.current_source_path}. Calling internal _player.play().")
            self._player.play()
            print("PLAYER_DEBUG: Internal _player.play() executed.")
        else:
            print("PLAYER_DEBUG: No current_source_path set. Play command ignored.")

    def pause(self):
        self._player.pause()

    def stop(self):
        self._player.stop()

    def set_volume(self, volume_percent): # 0-100
        # Convert 0-100 slider range to 0.0-1.0 QAudioOutput volume range
        self._audio_output.setVolume(float(volume_percent) / 100.0)

    def get_volume(self): # returns 0-100
        if self._audio_output:
            return int(self._audio_output.volume() * 100)
        else:
            return 0

    def set_position(self, position_ms):
        self._player.setPosition(position_ms)

    def get_position(self): # in ms
        return self._player.position()

    def get_duration(self): # in ms
        return self._player.duration()
    
    def playback_state(self):
        return self._player.playbackState()

    def is_metadata_available(self):
        try:
            media_status_ok = self._player.mediaStatus() in [
                QMediaPlayer.MediaStatus.LoadedMedia,
                QMediaPlayer.MediaStatus.BufferedMedia,
                QMediaPlayer.MediaStatus.BufferingMedia
            ]
            if not media_status_ok:
                # print("PLAYER_DEBUG: is_metadata_available: media_status not OK")
                return False

            # print("PLAYER_DEBUG: is_metadata_available: media_status OK, checking metaData object...")
            meta_data_obj = self._player.metaData() # Potential crash point
            # print(f"PLAYER_DEBUG: self._player.metaData() returned: {type(meta_data_obj)}")
            
            is_populated = bool(meta_data_obj)
            # print(f"PLAYER_DEBUG: is_metadata_available: metadata populated: {is_populated}")
            return is_populated
        except Exception as e:
            print(f"PLAYER_CRITICAL_ERROR in is_metadata_available: {e}")
            import traceback
            traceback.print_exc()
            return False

    def get_metadata(self, key_name):
        try:
            # print(f"PLAYER_DEBUG: get_metadata called for key: {key_name}")
            if not self.is_metadata_available():
                # print("PLAYER_DEBUG: Metadata not available for get_metadata")
                return ""

            key_map = {
                "Title": QMediaMetaData.Key.Title,
                "Artist": QMediaMetaData.Key.Author, # Or .AlbumArtist, .ContributingArtist
                "Album": QMediaMetaData.Key.AlbumTitle,
                "Duration": QMediaMetaData.Key.Duration
            }
            enum_key = key_map.get(key_name)
            
            # print("PLAYER_DEBUG: Attempting to get self._player.metaData() object in get_metadata")
            metadata = self._player.metaData() # Potential crash point
            # print(f"PLAYER_DEBUG: self._player.metaData() object in get_metadata is: {type(metadata)}")

            if enum_key and enum_key in metadata.keys(): # Corrected this line to check against metadata.keys()
                value = metadata.value(enum_key)
                # print(f"PLAYER_DEBUG: Found metadata for {key_name}: {value}")
                if key_name == "Duration" and isinstance(value, int):
                    return value # Return milliseconds as int
                return str(value) if value is not None else ""
            
            # print(f"PLAYER_DEBUG: Metadata NOT found for {key_name} (enum_key: {enum_key}, available_keys: {metadata.keys()})")
            return ""
        except Exception as e:
            print(f"PLAYER_CRITICAL_ERROR in get_metadata for key '{key_name}': {e}")
            import traceback
            traceback.print_exc()
            return "" # Return a default value in case of error

    def source_url(self):
        return self._player.source()

    def clear_source(self):
        self.current_source_path = None
        self._player.setSource(QUrl()) 