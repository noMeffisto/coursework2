class PlayerManager:
    def __init__(self):
        self.current_track = None

    def set_track(self, track):
        self.current_track = track
        print(f"Track set: {track['title']} - {track['artist']}")

    def play(self):
        if self.current_track:
            print(f"Playing: {self.current_track['title']} - {self.current_track['artist']}")
        else:
            print("No track selected!")

    def pause(self):
        if self.current_track:
            print(f"Paused: {self.current_track['title']} - {self.current_track['artist']}")
        else:
            print("No track selected!")