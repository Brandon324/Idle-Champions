# Idle Champions Automation Bot

A Python bot that automates clicking and progression in **Idle Champions of the Forgotten Realms**. It continuously scans the screen for coins, upgrades, and UI buttons, clicking them automatically so you can idle hands-free.

## Features

- Automatically collects coins (Blue, Green)
- Clicks all upgrade tiers (Red, Blue, Orange, Green, Purple, Pink)
- Handles UI buttons (Select, Close, Auto Progress, Complete, Skip, Continue)
- Configurable confidence threshold for image matching (works across different resolutions)
- Grayscale matching for reliability across color/theme variations
- Logging output so you can see what the bot is doing
- Clean stop with Ctrl+C

## Requirements

- Python 3.7+
- The game running in a **1280x720** window
- Dependencies:

```bash
pip install pyautogui opencv-python Pillow
```

> **Note:** `opencv-python` is required for the `confidence` and `grayscale` matching features. Without it, `pyautogui` falls back to exact pixel matching which is unreliable.

## Usage

1. Launch **Idle Champions of the Forgotten Realms** in a 1280x720 window
2. Run the bot:

```bash
python ldle_Champions.py
```

3. The bot will scan the screen in a loop, clicking any recognized elements
4. Press **Ctrl+C** to stop

## Configuration

Edit the constants at the top of `ldle_Champions.py` to tune behavior:

| Setting | Default | Description |
|---------|---------|-------------|
| `CONFIDENCE` | `0.7` | Image match threshold (0.0–1.0). Lower = more forgiving |
| `USE_GRAYSCALE` | `True` | Match in grayscale for better reliability |
| `CLICK_HOLD_TIME` | `0.3` | Seconds to pause after each click |
| `CYCLE_DELAY` | `2.0` | Seconds between full scan cycles |
| `SEARCH_DELAY` | `0.5` | Seconds between individual image searches |
| `FAILSAFE` | `False` | Set `True` to allow emergency stop by moving mouse to screen corner |

## Updating Screenshots

If the game updates its UI and the bot stops finding buttons, you can replace the PNG files:

1. Take a screenshot of the game element
2. Crop tightly around the button/icon
3. Save as PNG with the same filename (e.g., `BlueCoin.PNG`)
4. If confidence matching still fails, try lowering `CONFIDENCE` to `0.6`

## Project Structure

```
Idle-Champions/
├── ldle_Champions.py    # Main automation script
├── README.md
├── .gitignore
└── *.PNG                # Screenshot references for image matching
```
