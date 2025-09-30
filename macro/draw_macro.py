import pyautogui
import time
import os
from datetime import datetime
import keyboard
import requests
import threading
from dotenv import load_dotenv
import argparse
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_SCREENSHOT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "screenshots")
DEFAULT_FOLDER_PATH = r"D:\Maturaarbeit\Draws"

parser = argparse.ArgumentParser(description="Automate draws with PyAutoGUI and Telegram updates")
parser.add_argument("--num_draws", type=int, default=3, help="Number of draws to perform")
parser.add_argument("--receive_message_every", type=int, default=1, help="Send Telegram message every N draws")
parser.add_argument("--folder_path", type=str, default=DEFAULT_FOLDER_PATH, help="Folder to save Excel files")
parser.add_argument("--screenshot_dir", type=str, default=DEFAULT_SCREENSHOT_DIR, help="Folder with screenshots")
parser.add_argument("--bot_token", type=str, default=os.getenv("BOT_TOKEN"), help="Telegram bot token")
parser.add_argument("--chat_id", type=str, default=os.getenv("ID"), help="Telegram chat ID")

args = parser.parse_args()

config = {
    "num_draws": args.num_draws,
    "receive_message_every": args.receive_message_every,
    "folder_path": args.folder_path,
    "screenshot_dir": args.screenshot_dir,
    "telegram": {
        "bot_token": args.bot_token,
        "chat_id": args.chat_id
    }
}


# Load environment variables
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("ID")


# Event to signal stopping the automation
stop_event = threading.Event()

# Eigene Exception für Stopp
class AutomationCancelled(Exception):
    pass

def check_stop():
    if stop_event.is_set():
        raise AutomationCancelled("Automation cancelled through ESC.")
    
def safe_click(x, y):
    check_stop()
    pyautogui.moveTo(x, y)
    pyautogui.click()

def safe_press(key, times=1):
    for _ in range(times):
        check_stop()
        pyautogui.press(key)

# Telegram Bot
def send_telegram_message(message):
    telegram_config = config["telegram"]
    url = f"https://api.telegram.org/bot{telegram_config['bot_token']}/sendMessage"
    payload = {
        "chat_id": telegram_config["chat_id"],
        "text": message
    }
    try:
        response = requests.post(url, json=payload, timeout=5)
        if not response.ok:
            print(f"Error sending Telegram message: Status {response.status_code}")
    except requests.RequestException as e:
        print(f"Error: {e}")

# File storage setup
os.makedirs(config["folder_path"], exist_ok=True)
index_file = os.path.join(config["folder_path"], "draw_index.txt")

# Determine starting index for naming files
if os.path.exists(index_file):
    with open(index_file, "r") as file:
        content = file.read().strip()
        start_index = int(content) if content else 1
else:
    start_index = 1

# PyAutoGUI setup
pyautogui.PAUSE = 1  # Pause zwischen Aktionen
pyautogui.FAILSAFE = True  # Move mouse to top-left corner to abort

def wait_for_file(file_path, timeout=20, interval=0.5):
    start_time = time.monotonic()
    while time.monotonic() - start_time < timeout:
        if os.path.isfile(file_path):
            return True
        time.sleep(interval)
    print(f"Timeout! File {file_path} could not be found.")
    return False

# Automation functions
def safe_click_image(image_name, fallback_coords=None, confidence=0.8):
    check_stop()
    image_path = os.path.join(config["screenshot_dir"], image_name)
    location = pyautogui.locateOnScreen(image_path, confidence=confidence)
    if location:
        pyautogui.click(pyautogui.center(location))
        print(f"Clicked {image_path}")
    else:
        pyautogui.click(fallback_coords)
        print(f"{image_path} not found -> Fallback {fallback_coords} clicked")

def perform_draw():
    safe_click_image("draw.png", fallback_coords=(227, 53))
    safe_click_image("make_draw.png", fallback_coords=(285, 162))
    safe_click_image("next.png", fallback_coords=(992, 941))
    for _ in range(4):
        pyautogui.press("enter")
        time.sleep(0.1)

def export_draw():
    safe_click_image("draw.png", fallback_coords=(227, 53))
    safe_click_image("export_to_excel.png", fallback_coords=(310, 815))
    pyautogui.typewrite("")

def save_draw(full_path):
    pyautogui.typewrite(full_path)
    pyautogui.press("enter")

def finalize_draw():
    pyautogui.press("enter")

def esc_listener():
    keyboard.wait("esc")
    print("ESC detected")
    stop_event.set()

# Start ESC key listener
threading.Thread(target=esc_listener, daemon=True).start()
time.sleep(2)  # Delay before starting automation

cancelled = False
previous_filename = None

try:
    for i in range(config["num_draws"]):
        check_stop()

        current_index = start_index + i
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"Draw_{current_index}_{timestamp}.xlsx"
        full_path = os.path.join(config["folder_path"], filename)

        if i > 0 and previous_filename:
            if wait_for_file(os.path.join(config["folder_path"], previous_filename)):
                print(f"{previous_filename} was saved successfully")
            else:
                print(f"Error: {previous_filename} could NOT be saved")
                send_telegram_message(f"Error in draw {current_index}: File could NOT be saved")
                break

        perform_draw()
        export_draw()
        save_draw(full_path)
        time.sleep(2)
        finalize_draw()

        if current_index % config["receive_message_every"] == 0:
            send_telegram_message(f"Draw {current_index}/{start_index + config['num_draws'] - 1} completed.")

        with open(index_file, "w") as f:
            f.write(str(current_index + 1))

        previous_filename = filename

except AutomationCancelled as e:
    cancelled = True
    print(e)
    send_telegram_message("Automation cancelled.")

body = f"The script was stopped after {current_index}" if cancelled else f"All {current_index} draws were completed successfully"
send_telegram_message(body)
print("Done")
