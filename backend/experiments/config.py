class Settings:
    COUNT = 0

    def __init__(self):
        self.counter = Settings.get_count()
        print(f"Settings: initialize instance #{self.counter}")

    @classmethod
    def get_count(cls) -> int:
        cls.COUNT += 1
        return cls.COUNT

settings = Settings()    