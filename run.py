import subprocess, sys

for pkg in ["customtkinter"]:
    try:
        __import__(pkg.replace("-", "_"))
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", pkg])

from chrome_profile_launcher.app import Dashboard


def main():
    app = Dashboard()
    app.mainloop()


if __name__ == "__main__":
    main()
