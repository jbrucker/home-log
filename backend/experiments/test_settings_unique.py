"""Boilerplate code for creating a Settings instance and Engine instance
looks something like this:

```
class Settings:
    def __init__(self):
    # initialize attributes for settings

settings = Settings()
```
and other modules import this file.
This tests whether multiple imports create multiple instances.
"""   

from config import settings
import test_settings_unique_helper as helper

if __name__ == '__main__':
    print(f"My settings.counter = {settings.counter}")
    print(f"Helper settings.counter = {helper.get_settings().counter}")
    assert settings is helper.get_settings(), "Imported settings not the same"