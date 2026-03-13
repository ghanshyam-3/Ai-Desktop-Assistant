from AppOpener import open as app_opener, close as app_closer
import os

class AppLauncher:
    def __init__(self):
        # In a real scenario, we might want to cache this or run it async on startup
        # For now, AppOpener handles its own internal list.
        pass

    def open_app(self, app_name):
        """
        Attempts to open an application by name.
        Returns a tuple (success: bool, message: str)
        """
        if not app_name:
            return False, "No app name provided."

        print(f"Launcher: Opening {app_name}...")
        try:
            # match_closest=True helps with "google chrome" -> "chrome"
            app_opener(app_name, match_closest=True, throw_error=True)
            return True, f"Opening {app_name}"
        except Exception as e:
            print(f"Launcher Error: {e}")
            return False, f"Could not find {app_name}"

    def close_app(self, app_name):
        try:
            app_closer(app_name, match_closest=True, throw_error=True)
            return True, f"Closing {app_name}"
        except:
            return False, f"Could not close {app_name}"
