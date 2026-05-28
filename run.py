import subprocess, sys

try:
    import customtkinter
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "customtkinter"])
    import customtkinter

from chrome_profile_launcher.app import main

if __name__ == "__main__":
    main()
