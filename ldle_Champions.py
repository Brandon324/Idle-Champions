"""
Idle Champions of the Forgotten Realms - Automation Bot

Automates clicking coins, upgrades, and progression buttons in the game.
Uses screen image recognition with configurable confidence thresholds
and grayscale matching for reliability across different setups.
"""

import time
import sys
import logging
import pyautogui

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# Confidence threshold for image matching (0.0 - 1.0)
# Lower = more forgiving matches, Higher = stricter matches
# Start at 0.7 and increase if you get false positives
CONFIDENCE = 0.7

# Use grayscale matching (faster and more forgiving with color differences)
USE_GRAYSCALE = True

# Seconds to hold mouse down when clicking a found element
CLICK_HOLD_TIME = 0.3

# Seconds to wait between full scan cycles
CYCLE_DELAY = 2.0

# Seconds to wait between individual image searches within a cycle
SEARCH_DELAY = 0.5

# Disable pyautogui fail-safe (moving mouse to corner won't abort)
# Set to True during development so you can emergency-stop by moving mouse to corner
FAILSAFE = False

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("IdleChampions")

# ---------------------------------------------------------------------------
# Image lists — edit these if the game UI changes
# ---------------------------------------------------------------------------

COIN_IMAGES = [
    ("BlueCoin", "BlueCoin.PNG"),
    ("GreenCoin", "GreenCoin.PNG"),
]

UPGRADE_IMAGES = [
    ("RedUpgrade", "RedUpgrade.PNG"),
    ("BlueUpgrade", "BlueUpgrade.PNG"),
    ("BlueUpgradeV2", "BlueUpgradeV2.PNG"),
    ("OrangeUpgrade", "OrangeUpgrade.PNG"),
    ("GreenUpgrade", "GreenUpgrade.PNG"),
    ("PurpleUpgrade", "PurpleUpgrade.PNG"),
    ("PinkUpgrade", "PinkUpgrade.PNG"),
]

UI_IMAGES = [
    ("SelectButton", "SelectButton.PNG"),
    ("SelectButtonV2", "SelectButtonV2.PNG"),
    ("CloseButton", "CloseButton.PNG"),
    ("AutoProgress", "AutoProgress.PNG"),
    ("CompleteButton", "CompleteButton.PNG"),
    ("CompleteButtonV2", "CompleteButtonV2.PNG"),
    ("SkipButton", "SkipButton.PNG"),
    ("ContinueButton", "ContineButton.PNG"),
]

ALL_IMAGES = COIN_IMAGES + UPGRADE_IMAGES + UI_IMAGES

# ---------------------------------------------------------------------------
# Core helpers
# ---------------------------------------------------------------------------

pyautogui.FAILSAFE = FAILSAFE


def find_and_click(name, image_file):
    """Locate *image_file* on screen and click it. Returns True if found."""
    try:
        location = pyautogui.locateOnScreen(
            image_file,
            confidence=CONFIDENCE,
            grayscale=USE_GRAYSCALE,
        )
    except pyautogui.ImageNotFoundException:
        return False
    except Exception as exc:
        log.debug("Error searching for %s: %s", name, exc)
        return False

    if location is None:
        return False

    center = pyautogui.center(location)
    log.info("Found %-20s at (%d, %d) — clicking", name, center.x, center.y)
    pyautogui.click(center.x, center.y)
    time.sleep(CLICK_HOLD_TIME)
    return True


def click_all(image_list):
    """Try to find and click every image in *image_list* once per call."""
    for name, image_file in image_list:
        find_and_click(name, image_file)
        time.sleep(SEARCH_DELAY)


# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------

def run_cycle():
    """Run one full automation cycle: coins → upgrades → UI buttons."""
    log.info("--- Starting scan cycle ---")
    click_all(COIN_IMAGES)
    click_all(UPGRADE_IMAGES)
    click_all(UI_IMAGES)
    log.info("--- Cycle complete, sleeping %.1fs ---", CYCLE_DELAY)


def main():
    log.info("Idle Champions bot started (confidence=%.0f%%, grayscale=%s)",
             CONFIDENCE * 100, USE_GRAYSCALE)
    log.info("Press Ctrl+C to stop")
    try:
        while True:
            run_cycle()
            time.sleep(CYCLE_DELAY)
    except KeyboardInterrupt:
        log.info("Bot stopped by user")
        sys.exit(0)


if __name__ == "__main__":
    main()
