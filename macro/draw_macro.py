import pyautogui
import time
import os
from datetime import datetime
import keyboard
import requests
import threading
from dotenv import load_dotenv

# Number of draws to perform
num_draws = 3

# Send a Telegram message after every X draws
receive_message_every = 1

# Event to signal stopping the automation
stop_event = threading.Event()

# Telegram Bot for live updates
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("ID")

def send_telegram_message(message):
    telegram_token = BOT_TOKEN
    chat_id = CHAT_ID
    url = f"https://api.telegram.org/bot{telegram_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message
    }
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print("Error sending Telegram message: ", e)

# File storage setup
folder_path = r"D:\Maturaarbeit\Draws"
index_file = os.path.join(folder_path, "draw_index.txt")

# Determine starting index for naming files
if os.path.exists(index_file):
    with open(index_file, "r") as file:
        content = file.read().strip()
        if content == "":
            start_index = 1
        else:
            start_index = int(content)
else:
    start_index = 1

# PyAutoGUI setup
pyautogui.PAUSE = 1  # Pause between actions
pyautogui.FAILSAFE = True  # Move mouse to top-left corner to abort


# Automation functions

def perform_draw():
    pyautogui.moveTo(227, 53)
    pyautogui.leftClick()

    pyautogui.moveTo(285, 162)
    pyautogui.leftClick()

    pyautogui.moveTo(992, 941)
    pyautogui.leftClick()

    for _ in range(4):
        pyautogui.press("enter")
        time.sleep(0.1)

def export_draw():
    pyautogui.moveTo(227, 53)
    pyautogui.leftClick()

    pyautogui.moveTo(310, 815)
    pyautogui.leftClick()

    pyautogui.typewrite(f"")

def save_draw(full_path):
    pyautogui.typewrite(full_path)
    pyautogui.press("enter")

def finalize_draw():
    pyautogui.press("enter")

def esc_listener():
    # To cancel automation press enter
    keyboard.wait("esc")
    print("ESC detected")
    stop_event.set()

def wait_for_file(folder_path, filename, timeout=10):
    # Checks if the file before this one was saved. If it checked the current one, it never found the curernt one.
    file_path = os.path.join(folder_path, filename)
    if os.path.isfile(file_path):
        # print("Found in:", file_path)
        return True
    else:
        print(f"File {filename} not found in {folder_path}")
        return False




# Start ESC key listener in a separate thread
threading.Thread(target=esc_listener, daemon=True).start()

time.sleep(2)  # Delay before starting the automation

cancelled = False
previous_filename = None


# Main loop for performing draws
for i in range(num_draws):
    if stop_event.is_set():
        print("Automation was cancelled.")
        break

    current_index = start_index + i
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"Draw_{current_index}_{timestamp}.xlsx"
    full_path = os.path.join(folder_path, filename)

    # Check if the previous file was saved successfully
    if i > 0 and previous_filename:
        if wait_for_file(folder_path, previous_filename):
            print(f"{previous_filename} was saved successfully")
        else:
            print(f"Error: {previous_filename} could NOT be saved")
            send_telegram_message(f"Error in draw {current_index}: File could NOT be saved")
            break

    perform_draw()
    if stop_event.is_set():
        print("Automation was cancelled.")
        cancelled = True
        break

    export_draw()
    if stop_event.is_set():
        print("Automation was cancelled.")
        cancelled = True
        break

    save_draw(full_path)
    if stop_event.is_set():
        print("Automation was cancelled.")
        cancelled = True
        break

    time.sleep(2)  # Wait for file to be written

    finalize_draw()

    # Send Telegram update after every X draws
    if current_index % receive_message_every == 0:
        send_telegram_message(f"Draw {current_index}/{start_index + num_draws - 1} completed.")

    # Update index file for next run
    with open(index_file, "w") as f:
        f.write(str(current_index + 1))

    previous_filename = filename  # Store current file name for next iteration

# Final status message
if cancelled:
    body = f"The script was stopped after {current_index}"
else:
    body = f"All {current_index} draws were completed successfully"

send_telegram_message(body)
print("Done")
