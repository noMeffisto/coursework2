import logging

# Настраиваем логгер
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PlayerManager:
    def __init__(self):
        self.current_track = None

    def set_track(self, track):
        self.current_track = track
        logger.info(f"Track set: {track['title']} - {track['artist']}")

    def play(self):
        if self.current_track:
            logger.info(f"Playing: {self.current_track['title']} - {self.current_track['artist']}")
        else:
            logger.warning("No track selected!")

    def pause(self):
        if self.current_track:
            logger.info(f"Paused: {self.current_track['title']} - {self.current_track['artist']}")
        else:
            logger.warning("No track selected!")