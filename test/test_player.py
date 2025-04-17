import unittest
import sys
import os
import logging

# Добавляем корневую директорию проекта в sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core.player import PlayerManager

class TestPlayerManager(unittest.TestCase):
    def setUp(self):
        self.player_manager = PlayerManager()
        self.track = {"id": 1, "title": "Song 1", "artist": "Artist 1", "duration": 180}

    def test_set_track(self):
        # Тестируем установку трека
        self.player_manager.set_track(self.track)
        self.assertEqual(self.player_manager.current_track, self.track)

    def test_play_with_track(self):
        # Тестируем воспроизведение с установленным треком
        self.player_manager.set_track(self.track)
        with self.assertLogs(level='INFO') as cm:
            self.player_manager.play()
        self.assertIn("INFO:src.core.player:Playing: Song 1 - Artist 1", cm.output)

    def test_play_without_track(self):
        # Тестируем воспроизведение без трека
        with self.assertLogs(level='WARNING') as cm:
            self.player_manager.play()
        self.assertIn("WARNING:src.core.player:No track selected!", cm.output)

    def test_pause_with_track(self):
        # Тестируем паузу с установленным треком
        self.player_manager.set_track(self.track)
        with self.assertLogs(level='INFO') as cm:
            self.player_manager.pause()
        self.assertIn("INFO:src.core.player:Paused: Song 1 - Artist 1", cm.output)

    def test_pause_without_track(self):
        # Тестируем паузу без трека
        with self.assertLogs(level='WARNING') as cm:
            self.player_manager.pause()
        self.assertIn("WARNING:src.core.player:No track selected!", cm.output)

if __name__ == '__main__':
    unittest.main()