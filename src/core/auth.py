class AuthManager:
    def __init__(self):
        self.users = {
            "user1": {"password": "pass123", "name": "User One", "role": "user"},
            "guest": {"password": "", "name": "Guest", "role": "guest"}
        }

    def login(self, login, password):
        if login in self.users and self.users[login]["password"] == password:
            return self.users[login]  
        return None  