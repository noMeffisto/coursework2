import unittest
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core.auth import AuthManager

class TestAuthManager(unittest.TestCase):
    def setUp(self):
        self.auth_manager = AuthManager()

    def test_login_success(self):
        user = self.auth_manager.login("user1", "pass123")
        self.assertIsNotNone(user)
        self.assertEqual(user["role"], "user")
        self.assertEqual(user["name"], "User One")

    def test_login_guest(self):
        user = self.auth_manager.login("guest", "")
        self.assertIsNotNone(user)
        self.assertEqual(user["role"], "guest")
        self.assertEqual(user["name"], "Guest")

    def test_login_wrong_password(self):
        user = self.auth_manager.login("user1", "wrongpass")
        self.assertIsNone(user)

    def test_login_wrong_username(self):
        # Тестируем несуществующий логин
        user = self.auth_manager.login("unknown", "pass123")
        self.assertIsNone(user)

if __name__ == '__main__':
    unittest.main()