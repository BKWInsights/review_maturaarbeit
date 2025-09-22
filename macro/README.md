# Macro – Automated Tournament Draws

This Python script automates the generation of tournament draws in the Badminton Tournament Planner (BTP).  
It performs multiple draws, saves the results as Excel files, and sends status updates via Telegram.

---

## Features

- Performs a specified number of draws (`num_draws`)
- Saves each draw as a `.xlsx` file with timestamp and index
- Sends Telegram messages after X draws (optional)
- Intended to be stopped with the ESC key, but note: **the ESC listener does not stop the automation**.  
  Even though the message "ESC pressed" is printed, the automation continues.  
  To stop the script, you need to press **Ctrl + C** in the terminal.

---

## Dependencies

- Python 3.x
- `pyautogui` – mouse/keyboard automation
- `keyboard` – key listening
- `requests` – Telegram API calls
- `python-dotenv` – loading API keys from `.env`
- Standard libraries: `os`, `time`, `datetime`, `threading`

Install the Python packages with:

```bash
pip install pyautogui keyboard requests python-dotenv
```

---

## Usage

1. Prepare the environment
    - Ensure the Badminton Tournament Planner (BTP) is open.
    - Make sure the screen resolution matches the mouse coordinates used in the script (pyautogui.moveTo(x, y)). Adjust if necessary.
    - Create a folder for the output Excel files and set its path in folder_path.

2. Configure parameters
    - `num_draws` -> number of draws to perform
    - `receive_message_every` -> how often a Telegram message is sent
    - `folder_path` -> where Excel files will be 
    
3. Optional: Telegram messages
    - Create a .env file with your Telegram bot token and chat ID:
     ```env
    BOT_TOKEN=your_bot_token
    ID=your_chat_id
    ```

4. Run the script
```bash
python draw_macro.py
```

5. Stopping the script
    - Stops when `num_draws` have been made.
    - The ESC key listener does not stop the automation.
    - To cancel during the automation, press *Ctrl + C* in the terminal.