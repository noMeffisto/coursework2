from PyQt6.QtCore import QObject, pyqtSignal, QStandardPaths, QDir
import uuid # For unique playlist IDs
import json # Make sure json is imported
import os # Make sure os is imported

# These might be better in a shared config.py if used by multiple core modules
CONFIG_DIR_NAME = "MusicPlayerApp" 
CONFIG_FILE_NAME = "library_config.json"

class Playlist:
    def __init__(self, name, playlist_id=None):
        self.id = playlist_id if playlist_id else str(uuid.uuid4())
        self.name = name
        self.track_paths = [] # List of file_paths

    def add_track(self, file_path):
        if file_path not in self.track_paths:
            self.track_paths.append(file_path)
            return True
        return False

    def remove_track(self, file_path):
        if file_path in self.track_paths:
            self.track_paths.remove(file_path)
            return True
        return False

    def reorder_tracks(self, new_ordered_paths):
        # This method is called after QListWidget has already reordered its items.
        # We expect new_ordered_paths to be the new, complete list of track paths in the desired order.
        # The primary responsibility is to update self.track_paths.
        # Validation that the set of items hasn't changed can be a good sanity check,
        # but QListWidget with InternalMove should maintain the same set of items.
        
        # A simple check: if the counts are different, something is wrong upstream or our understanding.
        if len(new_ordered_paths) != len(self.track_paths):
            # This case should ideally not be hit if QListWidget's InternalMove works as expected
            # and no tracks were added/deleted by another means between drag and drop completion.
            print(f"Warning: Track count mismatch during reorder. Current: {len(self.track_paths)}, New: {len(new_ordered_paths)}. Proceeding with new order.")
            # Decide on behavior: reject, or accept the new list as authoritative.
            # For robustness with QListWidget, we might accept it, assuming QListWidget is the source of truth for its items.
        
        # Even more robust: check set equality if counts match and list is not empty
        # if len(new_ordered_paths) == len(self.track_paths) and self.track_paths: # Avoid set on empty lists if it causes issues
        #    if set(new_ordered_paths) != set(self.track_paths):
        #        print("Warning: Track set mismatch during reorder despite same count. Proceeding with new order.")
        #        # This would be a more serious inconsistency.

        self.track_paths = list(new_ordered_paths) # Ensure it's a new list copy
        return True
    
    def __repr__(self):
        return f"Playlist(id='{self.id}', name='{self.name}', tracks={len(self.track_paths)})"


class PlaylistManager(QObject):
    playlistsChanged = pyqtSignal() # Emitted when playlists are created, deleted, or modified significantly
    playlistTracksChanged = pyqtSignal(str) # Emitted with playlist_id when tracks within a playlist change
    playlistsLoaded = pyqtSignal() # Signal when playlists are loaded from disk

    def __init__(self, parent=None):
        super().__init__(parent)
        self._playlists = {} # {playlist_id: Playlist_object}
        self._config_path = self._get_config_file_path()
        self.load_playlists_from_disk() # Load playlists at startup

    def _get_config_file_path(self): # Helper, might be duplicated from LibraryManager
        config_dir_path = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppConfigLocation)
        if not config_dir_path:
            config_dir_path = os.path.join(os.path.expanduser("~"), ".MusicPlayerApp")
        
        app_config_dir = QDir(os.path.join(config_dir_path, CONFIG_DIR_NAME))
        if not app_config_dir.exists():
            app_config_dir.mkpath(".")
        return os.path.join(app_config_dir.absolutePath(), CONFIG_FILE_NAME)

    def create_playlist(self, name):
        if not name.strip():
            print("Playlist name cannot be empty.")
            return None

        for pl_id, pl in self._playlists.items():
            if pl.name == name:
                print(f"A playlist with the name '{name}' already exists.")
                return None
        
        # Create the new playlist object
        created_playlist = Playlist(name) # Create the playlist instance

        # Use the created object to add to the dictionary
        self._playlists[created_playlist.id] = created_playlist 
        
        self.playlistsChanged.emit()
        # self.save_playlists_to_disk() # Handled by MainWindow on close or specific actions
        print(f"Created playlist: {created_playlist}")
        return created_playlist

    def delete_playlist(self, playlist_id):
        if playlist_id in self._playlists:
            del self._playlists[playlist_id]
            self.playlistsChanged.emit()
            print(f"Deleted playlist ID: {playlist_id}")
            return True
        print(f"Playlist ID {playlist_id} not found for deletion.")
        return False

    def rename_playlist(self, playlist_id, new_name):
        if not new_name.strip():
            print("New playlist name cannot be empty.")
            return False
        if playlist_id in self._playlists:
            # Check for duplicate names (optional)
            for pid, pl in self._playlists.items():
                if pid != playlist_id and pl.name == new_name:
                    print(f"Another playlist with name '{new_name}' already exists.")
                    return False
            self._playlists[playlist_id].name = new_name
            self.playlistsChanged.emit()
            print(f"Renamed playlist ID {playlist_id} to '{new_name}'.")
            return True
        print(f"Playlist ID {playlist_id} not found for renaming.")
        return False

    def get_playlist_by_id(self, playlist_id):
        return self._playlists.get(playlist_id)

    def get_all_playlists(self):
        """Returns a list of all Playlist objects, typically sorted by name."""
        return sorted(self._playlists.values(), key=lambda p: p.name.lower())

    def add_track_to_playlist(self, playlist_id, track_file_path):
        playlist = self.get_playlist_by_id(playlist_id)
        if playlist:
            if playlist.add_track(track_file_path):
                self.playlistTracksChanged.emit(playlist_id)
                print(f"Added track {track_file_path} to playlist {playlist.name}")
                return True
        else:
            print(f"Playlist ID {playlist_id} not found for adding track.")
        return False

    def remove_track_from_playlist(self, playlist_id, track_file_path):
        playlist = self.get_playlist_by_id(playlist_id)
        if playlist:
            if playlist.remove_track(track_file_path):
                self.playlistTracksChanged.emit(playlist_id)
                print(f"Removed track {track_file_path} from playlist {playlist.name}")
                return True
        else:
            print(f"Playlist ID {playlist_id} not found for removing track.")
        return False

    def reorder_tracks_in_playlist(self, playlist_id, new_ordered_paths):
        """Reorders tracks in the specified playlist based on the new list of paths."""
        playlist = self.get_playlist_by_id(playlist_id)
        if not playlist:
            print(f"Playlist ID {playlist_id} not found for reordering tracks.")
            return False

        # The Playlist.reorder_tracks method already validates if the set of tracks is the same.
        if playlist.reorder_tracks(new_ordered_paths):
            print(f"Tracks reordered successfully in playlist '{playlist.name}' (ID: {playlist_id}).")
            self.playlistTracksChanged.emit(playlist_id) # Notify UI or other components
            return True
        else:
            print(f"Failed to reorder tracks in playlist '{playlist.name}'. Paths might mismatch or list empty.")
            # Optionally, emit a signal or raise an error to indicate failure more formally
            return False

    def save_playlists_to_disk(self):
        """Saves the current playlists to the JSON config file."""
        playlists_data = []
        for pl_id, playlist_obj in self._playlists.items():
            playlists_data.append({
                "id": pl_id,
                "name": playlist_obj.name,
                "track_paths": playlist_obj.track_paths
            })
        
        try:
            all_config_data = {}
            if os.path.exists(self._config_path):
                with open(self._config_path, 'r', encoding='utf-8') as f:
                    try:
                        all_config_data = json.load(f)
                    except json.JSONDecodeError:
                        print(f"Warning: Config file {self._config_path} is corrupted. Overwriting playlists section.")
                        pass # Will create a new structure or overwrite if file is totally corrupt
            
            all_config_data["playlists_data"] = playlists_data
            
            with open(self._config_path, 'w', encoding='utf-8') as f:
                json.dump(all_config_data, f, indent=4)
            print(f"Playlists saved to {self._config_path}")

        except IOError as e:
            print(f"Error saving playlists to {self._config_path}: {e}")

    def load_playlists_from_disk(self):
        """Loads playlists from the JSON config file."""
        if not os.path.exists(self._config_path):
            print(f"Playlists config not found in {self._config_path}. Starting with no playlists.")
            self.playlistsLoaded.emit()
            return

        try:
            with open(self._config_path, 'r', encoding='utf-8') as f:
                all_config_data = json.load(f)
            
            playlists_data = all_config_data.get("playlists_data", [])
            
            loaded_playlists_count = 0
            for pl_data in playlists_data:
                playlist_id = pl_data.get("id")
                name = pl_data.get("name")
                track_paths = pl_data.get("track_paths", [])
                
                if playlist_id and name:
                    # Basic validation for track paths (check if they exist)
                    # This could be slow if many tracks. Consider doing this on demand or with LibraryManager.
                    # valid_track_paths = [p for p in track_paths if os.path.exists(p)] 
                    # For now, load all paths as saved.
                    
                    loaded_playlist = Playlist(name, playlist_id=playlist_id)
                    loaded_playlist.track_paths = track_paths # Directly assign, could validate later
                    self._playlists[loaded_playlist.id] = loaded_playlist
                    loaded_playlists_count +=1
                else:
                    print(f"Skipping playlist load due to missing id or name: {pl_data}")
            
            if loaded_playlists_count > 0:
                print(f"Loaded {loaded_playlists_count} playlists.")
            # No self.playlistsChanged.emit() here, as that's for user-driven changes mostly.
            # Instead, a dedicated signal for UI to know loading is done.

        except (IOError, json.JSONDecodeError) as e:
            print(f"Error loading playlists from {self._config_path}: {e}. Starting with no playlists.")
            self._playlists.clear() # Ensure a clean state on error
        
        self.playlistsLoaded.emit()

    # Make sure methods that modify playlists call save_playlists_to_disk or rely on a save_on_exit strategy
    def delete_playlist(self, playlist_id):
        # ... (existing logic) ...
        if playlist_id in self._playlists:
            del self._playlists[playlist_id]
            self.playlistsChanged.emit()
            # self.save_playlists_to_disk()
            print(f"Deleted playlist ID: {playlist_id}")
        # ... (existing logic) ...

    def rename_playlist(self, playlist_id, new_name):
        # ... (existing logic) ...
        if playlist_id in self._playlists:
            # Check for duplicate names (optional)
            for pid, pl in self._playlists.items():
                if pid != playlist_id and pl.name == new_name:
                    print(f"Another playlist with name '{new_name}' already exists.")
                    return False
            self._playlists[playlist_id].name = new_name
            self.playlistsChanged.emit()
            # self.save_playlists_to_disk()
            print(f"Renamed playlist ID {playlist_id} to '{new_name}'.")
        # ... (existing logic) ...

    def add_track_to_playlist(self, playlist_id, track_file_path):
        # ... (existing logic) ...
        playlist = self.get_playlist_by_id(playlist_id)
        if playlist:
            if playlist.add_track(track_file_path):
                self.playlistTracksChanged.emit(playlist_id)
                # self.save_playlists_to_disk()
                print(f"Added track {track_file_path} to playlist {playlist.name}")
        # ... (existing logic) ...

    def remove_track_from_playlist(self, playlist_id, track_file_path):
        # ... (existing logic) ...
        playlist = self.get_playlist_by_id(playlist_id)
        if playlist:
            if playlist.remove_track(track_file_path):
                self.playlistTracksChanged.emit(playlist_id)
                # self.save_playlists_to_disk()
                print(f"Removed track {track_file_path} from playlist {playlist.name}")
        # ... (existing logic) ...

    # Placeholder for saving and loading - to be implemented next
    def save_playlists(self, config_path):
        pass

    def load_playlists(self, config_path):
        pass 