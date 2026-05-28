import subprocess
import sys

try:
    import customtkinter
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "customtkinter"])
    import customtkinter

try:
    import requests
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "requests"])
    import requests

from chrome_profile_launcher.app import LoginWindow, Dashboard


def main():
    login = LoginWindow()
    result = login.run()
    if result:
        app = Dashboard()
        app.mainloop()
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
