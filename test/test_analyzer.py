import unittest
import sys
import os


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core.analyzer import Analyzer

class TestAnalyzer(unittest.TestCase):
    def setUp(self):
        self.analyzer = Analyzer()
        self.track = {"id": 1, "title": "Song 1", "artist": "Artist 1", "duration": 180}

    def test_analyze_with_track(self):
        # Тестируем анализ с треком
        result = self.analyzer.analyze(self.track)
        expected = "Analysis for Song 1 - Artist 1: Frequency = 440Hz, Intensity = 0.5 (placeholder)"
        self.assertEqual(result, expected)

    def test_analyze_without_track(self):
        # Тестируем анализ без трека
        result = self.analyzer.analyze(None)
        self.assertEqual(result, "No track selected for analysis!")

if __name__ == '__main__':
    unittest.main()