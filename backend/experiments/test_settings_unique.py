"""Test whether an instance created in a module is created each time \
   the module is imported or created only once.

The config module (config.py) creates a Settings instance like this:

```
class Settings:
    def __init__(self):
    # initialize attributes for settings

settings = Settings()
```
and other modules import this file. The "database" module creates
an 'engine' with similar code.

Answer: `settings` is created only once.
"""

from config import settings
import test_settings_unique_helper as helper

if __name__ == '__main__':
    print(f"My settings.counter = {settings.counter}")
    print(f"Helper settings.counter = {helper.get_settings().counter}")
    assert settings is helper.get_settings(), "Imported settings not the same"
    assert settings is helper.get_settings()
    print("The 'Settings' instance appears to be created only once.")
