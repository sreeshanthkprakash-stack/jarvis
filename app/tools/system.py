import datetime
import platform
import shutil
import subprocess
import os

import pyautogui


def get_time():
    now = datetime.datetime.now()
    return now.strftime("%I:%M %p")


def get_date():
    now = datetime.datetime.now()
    return now.strftime("%A, %B %d, %Y")


def get_system_info():
    disk = shutil.disk_usage("C:\\")

    return {
        "operating_system": platform.system(),
        "release": platform.release(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "disk_free_gb": round(
            disk.free / (1024 ** 3),
            2
        ),
    }


def lock_computer():
    try:
        subprocess.Popen(
            [
                "rundll32.exe",
                "user32.dll,LockWorkStation"
            ],
            creationflags=subprocess.CREATE_NO_WINDOW
        )

        return "Locking the computer."

    except Exception as error:
        return f"I couldn't lock the computer. Error: {error}"


def sleep_computer():
    try:
        subprocess.Popen(
            [
                "powershell.exe",
                "-NoProfile",
                "-Command",
                "Start-Sleep -Seconds 1; "
                "Add-Type -AssemblyName System.Windows.Forms; "
                "[System.Windows.Forms.Application]::SetSuspendState("
                "3, $false, $false)"
            ],
            creationflags=subprocess.CREATE_NO_WINDOW
        )

        return "Putting the computer to sleep."

    except Exception as error:
        return f"I couldn't put the computer to sleep. Error: {error}"


def volume_up():
    try:
        subprocess.run(
            [
                "powershell.exe",
                "-NoProfile",
                "-Command",
                "$wshell = New-Object -ComObject WScript.Shell; "
                "$wshell.SendKeys([char]175)"
            ],
            creationflags=subprocess.CREATE_NO_WINDOW
        )

        return "Volume increased."

    except Exception as error:
        return f"I couldn't increase the volume. Error: {error}"


def volume_down():
    try:
        subprocess.run(
            [
                "powershell.exe",
                "-NoProfile",
                "-Command",
                "$wshell = New-Object -ComObject WScript.Shell; "
                "$wshell.SendKeys([char]174)"
            ],
            creationflags=subprocess.CREATE_NO_WINDOW
        )

        return "Volume decreased."

    except Exception as error:
        return f"I couldn't decrease the volume. Error: {error}"


def mute_volume():
    try:
        subprocess.run(
            [
                "powershell.exe",
                "-NoProfile",
                "-Command",
                "$wshell = New-Object -ComObject WScript.Shell; "
                "$wshell.SendKeys([char]173)"
            ],
            creationflags=subprocess.CREATE_NO_WINDOW
        )

        return "Volume muted."

    except Exception as error:
        return f"I couldn't mute the volume. Error: {error}"


def take_screenshot():
    try:
        from PIL import ImageGrab

        screenshot_dir = (
            r"C:\Users\SREESHANTH_K\Documents\Screenshots"
        )

        os.makedirs(
            screenshot_dir,
            exist_ok=True
        )

        filename = datetime.datetime.now().strftime(
            "screenshot_%Y%m%d_%H%M%S.png"
        )

        path = os.path.join(
            screenshot_dir,
            filename
        )

        screenshot = ImageGrab.grab()
        screenshot.save(path)

        return f"Screenshot saved to {path}."

    except Exception as error:
        return (
            f"I couldn't take a screenshot. "
            f"Error: {error}"
        )


def get_clipboard():
    try:
        import pyperclip

        content = pyperclip.paste()

        if not content:
            return "The clipboard is empty."

        return content

    except Exception as error:
        return (
            f"I couldn't read the clipboard. "
            f"Error: {error}"
        )


def set_clipboard(text):
    try:
        import pyperclip

        pyperclip.copy(text)

        return "Copied to the clipboard."

    except Exception as error:
        return (
            f"I couldn't write to the clipboard. "
            f"Error: {error}"
        )