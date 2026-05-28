import subprocess, sys

for pkg in ["customtkinter"]:
    try:
        __import__(pkg.replace("-", "_"))
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", pkg])

from chrome_profile_launcher.app import ActivationWindow, Dashboard


def main():
    win = ActivationWindow()
    ok = win.run()
    if ok:
        app = Dashboard(licensed=True)
        app.mainloop()
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
