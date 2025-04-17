class LibraryManager:
    def __init__(self):
        self.tracks = [
            {"id": 1, "title": "Song 1", "artist": "Artist 1", "duration": 180},
            {"id": 2, "title": "Song 2", "artist": "Artist 2", "duration": 200}
        ]

    def get_tracks(self):
        return self.tracks

    def add_track(self, track):
        self.tracks.append(track)

    def remove_track(self, track_id):
        self.tracks = [t for t in self.tracks if t["id"] != track_id]