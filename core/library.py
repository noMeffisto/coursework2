import os
import json
import mutagen
from dataclasses import dataclass, field
from PyQt6.QtCore import QObject, pyqtSignal, QStandardPaths, QDir

CONFIG_DIR_NAME = "MusicPlayerApp"
CONFIG_FILE_NAME = "library_config.json"

@dataclass
class Track:
    file_path: str
    title: str
    artist: str
    album: str
    duration_ms: int = 0

class MusicLibraryManager(QObject):
    libraryLoaded = pyqtSignal()
    libraryUpdated = pyqtSignal(list)
    scanProgress = pyqtSignal(int, str)

    SUPPORTED_EXTENSIONS = [".mp3", ".wav", ".flac", ".aac", ".m4a", ".ogg"]

    def __init__(self, parent=None):
        super().__init__(parent)
        self._tracks = {} 
        self._library_folders = set()
        self._config_path = self._get_config_file_path()
        self.load_library_from_disk()

    def _get_config_file_path(self):
        config_dir_path = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppConfigLocation)
        if not config_dir_path:
            config_dir_path = os.path.join(os.path.expanduser("~"), ".MusicPlayerApp")
        
        app_config_dir = QDir(os.path.join(config_dir_path, CONFIG_DIR_NAME))
        if not app_config_dir.exists():
            app_config_dir.mkpath(".")
        return os.path.join(app_config_dir.absolutePath(), CONFIG_FILE_NAME)

    def add_library_folder(self, folder_path):
        if folder_path and os.path.isdir(folder_path):
            self._library_folders.add(folder_path)
            print(f"Added library folder: {folder_path}")
            return True
        return False

    def remove_folder(self, folder_path_to_remove):
        if folder_path_to_remove in self._library_folders:
            self._library_folders.discard(folder_path_to_remove)
            
            tracks_to_remove = [fp for fp, track in self._tracks.items() if track.file_path.startswith(folder_path_to_remove)]
            for fp in tracks_to_remove:
                del self._tracks[fp]
            print(f"Removed folder {folder_path_to_remove} and its tracks from library.")
            self.libraryUpdated.emit(self.get_all_tracks_for_ui_update()) 
            return True
        return False

    def get_library_folders(self):
        return list(self._library_folders)

    def scan_folder(self, folder_path, existing_track_paths_in_view=None):
        if existing_track_paths_in_view is None:
            existing_track_paths_in_view = set()

        newly_added_tracks_data = [] 
        files_scanned = 0
        
        print(f"Scanning folder: {folder_path}")
        for dirpath, _, filenames in os.walk(folder_path):
            for filename in filenames:
                file_path = os.path.join(dirpath, filename)
                files_scanned += 1
                self.scanProgress.emit(files_scanned, file_path)

                if file_path.lower().endswith(tuple(self.SUPPORTED_EXTENSIONS)):
                    if file_path in self._tracks or file_path in existing_track_paths_in_view:
                        continue 

                    try:
                        audio = mutagen.File(file_path, easy=True)
                        if audio is None:
                            print(f"Warning: Could not read metadata for {file_path} (mutagen returned None)")
                            continue

                        title = audio.get('title', [os.path.splitext(os.path.basename(file_path))[0]])[0]
                        artist = audio.get('artist', ["Unknown Artist"])[0]
                        album = audio.get('album', ["Unknown Album"])[0]
                        
                        duration_ms = 0
                        if hasattr(audio, 'info') and audio.info and hasattr(audio.info, 'length'):
                            duration_ms = int(audio.info.length * 1000)
                        
                        track_obj = Track(
                            file_path=file_path,
                            title=title if title else os.path.splitext(os.path.basename(file_path))[0],
                            artist=artist if artist else "Unknown Artist",
                            album=album if album else "Unknown Album",
                            duration_ms=duration_ms
                        )
                        self._tracks[file_path] = track_obj
                        newly_added_tracks_data.append({
                            'text': f"{track_obj.title} - {track_obj.artist} ({track_obj.album})",
                            'file_path': track_obj.file_path,
                            'duration_ms': track_obj.duration_ms
                        })
                    except mutagen.MutagenError as e:
                        print(f"Error reading metadata for {file_path}: {e}")
                    except Exception as e:
                        print(f"Generic error processing file {file_path}: {e}")
        print(f"Finished scanning {folder_path}. Found {len(newly_added_tracks_data)} new tracks.")
        return newly_added_tracks_data

    def scan_all_library_folders(self):
        print(f"Rescanning library folders: {self._library_folders}")
        all_new_tracks_data = []
        if not self._library_folders:
            print("No library folders set to scan.")
            self.libraryUpdated.emit([])
            return
        
        current_track_paths_in_view = {track.file_path for track in self._tracks.values()}

        for folder in list(self._library_folders): 
            if not os.path.isdir(folder):
                print(f"Warning: Library folder {folder} no longer exists. Removing from list.")
                self._library_folders.discard(folder)
                continue
            new_tracks_from_folder = self.scan_folder(folder, existing_track_paths_in_view=current_track_paths_in_view)
            all_new_tracks_data.extend(new_tracks_from_folder)
            current_track_paths_in_view.update(d['file_path'] for d in new_tracks_from_folder)

        if all_new_tracks_data:
            print(f"Total new tracks added from rescan: {len(all_new_tracks_data)}")
            self.libraryUpdated.emit(all_new_tracks_data) 
        else:
            print("No new tracks found during rescan.")
            self.libraryUpdated.emit([]) 

    def get_track_by_path(self, file_path):
        return self._tracks.get(file_path)

    def get_all_tracks_sorted(self):
        return sorted(self._tracks.values(), key=lambda track: (track.artist.lower(), track.album.lower(), track.title.lower()))

    def get_all_tracks_for_ui_update(self):
        return [
            {
                'text': f"{track.title} - {track.artist} ({track.album})", 
                'file_path': track.file_path,
                'duration_ms': track.duration_ms
            } 
            for track in self.get_all_tracks_sorted()
        ]

    def remove_track_by_path(self, file_path):
        if file_path in self._tracks:
            del self._tracks[file_path]
            print(f"Track {file_path} removed from library manager.")
            return True
        return False

    def save_library_to_disk(self):
        print(f"Attempting to save library. Config path: {self._config_path}")
        if not self._config_path:
            print("Error: Config path not set. Cannot save library.")
            return

        library_data_to_save = {
            "library_folders": list(self._library_folders),
            "tracks_cache": [
                {
                    "file_path": track.file_path, 
                    "title": track.title, 
                    "artist": track.artist, 
                    "album": track.album,
                    "duration_ms": track.duration_ms
                } 
                for track in self._tracks.values()
            ]
        }
        
        try:
            all_config_data = {}
            if os.path.exists(self._config_path):
                try:
                    with open(self._config_path, 'r', encoding='utf-8') as f:
                        all_config_data = json.load(f)
                except json.JSONDecodeError:
                    print(f"Warning: Config file {self._config_path} is corrupted. Will create new or overwrite.")
            
            all_config_data.update(library_data_to_save)

            config_dir = os.path.dirname(self._config_path)
            if not os.path.exists(config_dir):
                os.makedirs(config_dir, exist_ok=True)
                print(f"Created directory: {config_dir}")
            
            with open(self._config_path, 'w', encoding='utf-8') as f:
                json.dump(all_config_data, f, indent=4)
            print(f"Library saved to {self._config_path}")

        except IOError as e:
            print(f"Error saving library to {self._config_path}: {e}")
        except Exception as e:
            print(f"An unexpected error occurred while saving library: {e}")

    def load_library_from_disk(self):
        if not os.path.exists(self._config_path):
            print(f"Library config not found at {self._config_path}. Starting with an empty library.")
            self.libraryLoaded.emit() 
            return

        try:
            with open(self._config_path, 'r', encoding='utf-8') as f:
                all_config_data = json.load(f)
            
            self._library_folders = set(all_config_data.get("library_folders", []))
            print(f"Loaded library folders: {self._library_folders}")

            tracks_cache_data = all_config_data.get("tracks_cache", [])
            loaded_tracks_count = 0
            valid_tracks_to_load = {}
            for track_data in tracks_cache_data:
                if not isinstance(track_data, dict):
                    print(f"LYRICS_DEBUG: Skipping invalid cache entry (not a dict): {track_data}")
                    continue
                fp = track_data.get("file_path")
                if fp and os.path.exists(fp): 
                    track = Track(
                        file_path=fp,
                        title=track_data.get("title", "Unknown Title"),
                        artist=track_data.get("artist", "Unknown Artist"),
                        album=track_data.get("album", "Unknown Album"),
                        duration_ms=track_data.get("duration_ms", 0)
                    )
                    valid_tracks_to_load[fp] = track
                    loaded_tracks_count += 1
                elif fp:
                    print(f"Track path {fp} from cache does not exist. Skipping.")
            
            self._tracks = valid_tracks_to_load
            if loaded_tracks_count > 0:
                print(f"Loaded {loaded_tracks_count} tracks from cache.")
            else:
                print("No valid tracks found in cache or cache was empty.")

        except (IOError, json.JSONDecodeError) as e:
            print(f"Error loading library from {self._config_path}: {e}. Starting with an empty library.")
            self._tracks.clear()
            self._library_folders.clear()
        except Exception as e:
            print(f"An unexpected error occurred while loading library: {e}. Starting with an empty library.")
            self._tracks.clear()
            self._library_folders.clear()
        
        self.libraryLoaded.emit() 