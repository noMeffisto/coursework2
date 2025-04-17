import unittest
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core.library import LibraryManager

class TestLibraryManager(unittest.TestCase):
    def setUp(self):
        self.library_manager = LibraryManager()

    def test_get_tracks(self):
        # Тестируем получение списка треков
        tracks = self.library_manager.get_tracks()
        self.assertEqual(len(tracks), 2)  # Изначально 2 трека
        self.assertEqual(tracks[0]["title"], "Song 1")
        self.assertEqual(tracks[1]["artist"], "Artist 2")

    def test_add_track(self):
        # Тестируем добавление трека
        new_track = {"id": 3, "title": "New Song", "artist": "New Artist", "duration": 150}
        self.library_manager.add_track(new_track)
        tracks = self.library_manager.get_tracks()
        self.assertEqual(len(tracks), 3)  # Теперь 3 трека
        self.assertEqual(tracks[-1]["title"], "New Song")

    def test_remove_track(self):
        # Тестируем удаление трека
        self.library_manager.remove_track(1)  # Удаляем трек с id=1
        tracks = self.library_manager.get_tracks()
        self.assertEqual(len(tracks), 1)  # Остался 1 трек
        self.assertEqual(tracks[0]["id"], 2)  # Трек с id=2 должен остаться

if __name__ == '__main__':
    unittest.main()