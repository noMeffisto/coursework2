from PyQt5.QtMultimedia import QMediaPlayer

class PlayerManager:
    def __init__(self):
        self.player = QMediaPlayer()

    def play(self):
        self.player.play()

    def pause(self):
        self.player.pause()