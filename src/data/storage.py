class Storage:
    def __init__(self):
        self.data = {"users": {}, "tracks": []}

    def save(self, key, value):
        self.data[key] = value

    def load(self, key):
        return self.data.get(key, {})