import os
import sys
import subprocess


def build_binary():
    command = [
        "pyinstaller",
        "--onefile",  # Single executable
        "--windowed",  # No console window
        "--name",
        "GLL2TXT_Converter",
        "app.py",
    ]

    try:
        result = subprocess.run(command, capture_output=True, text=True)
        print("Build Output:", result.stdout)
        print("Build Errors:", result.stderr)
    except Exception as e:
        print(f"Build failed: {e}")


if __name__ == "__main__":
    build_binary()
