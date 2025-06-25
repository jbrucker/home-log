"""Is the settings variable instantiated only once, 
   or each time the module is imported?

   Answer: It is instantiated only once.
"""
class Settings:
    COUNT = 0  # class variable

    def __init__(self):
        self.counter = Settings.get_count()
        print(f"Settings: initialize instance #{self.counter}")

    @classmethod
    def get_count(cls) -> int:
        cls.COUNT += 1
        return cls.COUNT

settings = Settings()    