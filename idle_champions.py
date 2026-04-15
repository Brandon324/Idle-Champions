"""
Idle Champions of the Forgotten Realms - Automation Bot

A feature-rich bot for automating Idle Champions. Includes:
- Configurable image matching with confidence + grayscale
- Game window auto-detection and region-limited scanning
- Dry-run mode, retry logic, stuck detection
- Priority click ordering for time-sensitive buttons
- Scheduling, notifications, session stats, file logging
- Multi-resolution image sets, formation save/load
- Live GUI overlay with stop button
- Adventure auto-restart via priority ordering

Usage:
    python idle_champions.py                  # run with config.json
    python idle_champions.py --dry-run        # scan without clicking
    python idle_champions.py --schedule 4     # run for 4 hours
    python idle_champions.py --confidence 0.6 # override match threshold
    python idle_champions.py --list-formations
"""

import argparse
import datetime
import json
import logging
import threading
import time
from collections import defaultdict
from pathlib import Path

import pyautogui

# ---------------------------------------------------------------------------
# Optional dependencies (degrade gracefully if missing)
# ---------------------------------------------------------------------------

try:
    import cv2  # noqa: F401  (pyautogui uses opencv internally for confidence)
    HAS_OPENCV = True
except ImportError:
    HAS_OPENCV = False

try:
    import pygetwindow as gw
    HAS_GETWINDOW = True
except ImportError:
    HAS_GETWINDOW = False

try:
    from plyer import notification
    HAS_PLYER = True
except ImportError:
    HAS_PLYER = False

try:
    import tkinter as tk
    HAS_TKINTER = True
except ImportError:
    HAS_TKINTER = False


# ---------------------------------------------------------------------------
# Image definitions organized by priority category
# ---------------------------------------------------------------------------

IMAGE_CATEGORIES = {
    # Time-sensitive buttons first — adventure completion and progression
    "complete": [
        ("CompleteButton", "CompleteButton.PNG"),
        ("CompleteButtonV2", "CompleteButtonV2.PNG"),
    ],
    "skip": [
        ("SkipButton", "SkipButton.PNG"),
    ],
    "continue": [
        ("ContinueButton", "ContineButton.PNG"),
    ],
    # Resource collection
    "coins": [
        ("BlueCoin", "BlueCoin.PNG"),
        ("GreenCoin", "GreenCoin.PNG"),
    ],
    # Upgrade buttons
    "upgrades": [
        ("RedUpgrade", "RedUpgrade.PNG"),
        ("BlueUpgrade", "BlueUpgrade.PNG"),
        ("BlueUpgradeV2", "BlueUpgradeV2.PNG"),
        ("OrangeUpgrade", "OrangeUpgrade.PNG"),
        ("GreenUpgrade", "GreenUpgrade.PNG"),
        ("PurpleUpgrade", "PurpleUpgrade.PNG"),
        ("PinkUpgrade", "PinkUpgrade.PNG"),
    ],
    # Secondary UI
    "ui": [
        ("SelectButton", "SelectButton.PNG"),
        ("SelectButtonV2", "SelectButtonV2.PNG"),
        ("CloseButton", "CloseButton.PNG"),
        ("AutoProgress", "AutoProgress.PNG"),
    ],
}


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

class Config:
    """Load config from config.json, apply CLI overrides."""

    DEFAULTS = {
        "confidence": 0.7,
        "use_grayscale": True,
        "click_hold_time": 0.3,
        "cycle_delay": 2.0,
        "search_delay": 0.3,
        "failsafe": False,
        "resolution": "1280x720",
        "image_dir": "images",
        "log_dir": "logs",
        "formation_dir": "formations",
        "dry_run": False,
        "max_retries": 3,
        "stuck_threshold": 10,
        "schedule_hours": 0,
        "priority_order": [
            "complete", "skip", "continue", "coins", "upgrades", "ui",
        ],
        "enable_notifications": True,
        "enable_gui": True,
        "log_to_file": True,
        "auto_restart_adventure": True,
    }

    def __init__(self, config_path="config.json"):
        self._data = dict(self.DEFAULTS)
        self._path = config_path
        self._load_file()

    def _load_file(self):
        path = Path(self._path)
        if path.exists():
            try:
                with open(path) as f:
                    file_data = json.load(f)
                self._data.update(file_data)
            except (json.JSONDecodeError, OSError) as exc:
                print(f"[WARN] Could not load {path}: {exc}. Using defaults.")

    def apply_overrides(self, overrides):
        for key, value in overrides.items():
            if value is not None:
                self._data[key] = value

    def __getattr__(self, name):
        if name.startswith("_"):
            raise AttributeError(name)
        try:
            return self._data[name]
        except KeyError:
            raise AttributeError(f"No config option '{name}'")


# ---------------------------------------------------------------------------
# Session stats
# ---------------------------------------------------------------------------

class Stats:
    def __init__(self):
        self.start_time = datetime.datetime.now()
        self.clicks = defaultdict(int)
        self.cycles = 0
        self.total_found = 0
        self.total_missed = 0

    def record_click(self, name):
        self.clicks[name] += 1
        self.total_found += 1

    def record_miss(self):
        self.total_missed += 1

    def record_cycle(self):
        self.cycles += 1

    @property
    def runtime(self):
        return datetime.datetime.now() - self.start_time

    def summary(self):
        lines = [
            "=" * 40,
            "  Session Summary",
            "=" * 40,
            f"Runtime:     {str(self.runtime).split('.')[0]}",
            f"Cycles:      {self.cycles}",
            f"Total hits:  {self.total_found}",
            f"Empty scans: {self.total_missed}",
            "",
            "Clicks by element:",
        ]
        if self.clicks:
            for name, count in sorted(self.clicks.items(), key=lambda x: -x[1]):
                lines.append(f"  {name:<20} {count}")
        else:
            lines.append("  (none)")
        lines.append("=" * 40)
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Desktop notifications
# ---------------------------------------------------------------------------

class Notifier:
    def __init__(self, enabled=True):
        self.enabled = enabled and HAS_PLYER

    def notify(self, title, message):
        if not self.enabled:
            return
        try:
            notification.notify(
                title=title,
                message=message,
                app_name="Idle Champions Bot",
                timeout=5,
            )
        except Exception:
            pass  # notifications are nice-to-have; never crash on them


# ---------------------------------------------------------------------------
# Game window detection (for region-limited scanning)
# ---------------------------------------------------------------------------

class WindowDetector:
    WINDOW_TITLE_KEYWORD = "idle champions"

    def __init__(self):
        self.region = None  # (left, top, width, height) or None for full screen

    def find_game_window(self):
        if not HAS_GETWINDOW:
            return None
        try:
            for w in gw.getAllWindows():
                if (w.title
                        and self.WINDOW_TITLE_KEYWORD in w.title.lower()
                        and w.width > 0 and w.height > 0):
                    self.region = (w.left, w.top, w.width, w.height)
                    return self.region
        except Exception:
            pass
        return None


# ---------------------------------------------------------------------------
# Formation manager
# ---------------------------------------------------------------------------

class FormationManager:
    def __init__(self, formation_dir="formations"):
        self.formation_dir = Path(formation_dir)
        self.formation_dir.mkdir(parents=True, exist_ok=True)

    def save(self, name, data):
        path = self.formation_dir / f"{name}.json"
        with open(path, "w") as f:
            json.dump(data, f, indent=2)
        return path

    def load(self, name):
        path = self.formation_dir / f"{name}.json"
        if path.exists():
            with open(path) as f:
                return json.load(f)
        return None

    def list_formations(self):
        return sorted(p.stem for p in self.formation_dir.glob("*.json"))


# ---------------------------------------------------------------------------
# GUI overlay (live stats + stop button)
# ---------------------------------------------------------------------------

class GUIOverlay:
    def __init__(self, stats):
        self.stats = stats
        self.running = False
        self.root = None
        self.thread = None
        self.status_var = None
        self.stop_callback = None

    def start(self, stop_callback=None):
        if not HAS_TKINTER:
            return
        self.stop_callback = stop_callback
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def _run(self):
        try:
            self.root = tk.Tk()
        except Exception:
            return  # no display available
        self.root.title("IC Bot")
        self.root.attributes("-topmost", True)
        self.root.geometry("280x220")
        self.root.resizable(False, False)
        self.root.configure(bg="#1e1e1e")

        title = tk.Label(
            self.root, text="Idle Champions Bot",
            font=("Arial", 11, "bold"), fg="#00cc66", bg="#1e1e1e",
        )
        title.pack(pady=(8, 4))

        self.status_var = tk.StringVar(value="Starting...")
        status = tk.Label(
            self.root, textvariable=self.status_var,
            font=("Courier", 9), fg="#cccccc", bg="#1e1e1e",
            justify=tk.LEFT, anchor="w",
        )
        status.pack(fill=tk.X, padx=10, pady=4)

        btn_frame = tk.Frame(self.root, bg="#1e1e1e")
        btn_frame.pack(pady=8)
        stop_btn = tk.Button(
            btn_frame, text="Stop Bot", command=self._stop,
            bg="#cc3333", fg="white", font=("Arial", 10, "bold"), width=12,
        )
        stop_btn.pack()

        self.running = True
        self._update_display()
        self.root.protocol("WM_DELETE_WINDOW", self._stop)
        self.root.mainloop()

    def _update_display(self):
        if not self.running or not self.root:
            return
        s = self.stats
        text = (
            f"Runtime:  {str(s.runtime).split('.')[0]}\n"
            f"Cycles:   {s.cycles}\n"
            f"Clicks:   {s.total_found}\n"
            f"Top: {self._top_clicks()}"
        )
        try:
            self.status_var.set(text)
            self.root.after(1000, self._update_display)
        except Exception:
            pass

    def _top_clicks(self):
        if not self.stats.clicks:
            return "none yet"
        top = sorted(self.stats.clicks.items(), key=lambda x: -x[1])[:3]
        return ", ".join(f"{n}:{c}" for n, c in top)

    def _stop(self):
        self.running = False
        if self.stop_callback:
            self.stop_callback()
        try:
            if self.root:
                self.root.destroy()
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Main bot
# ---------------------------------------------------------------------------

class IdleChampionsBot:
    def __init__(self, config):
        self.config = config
        self.stats = Stats()
        self.notifier = Notifier(config.enable_notifications)
        self.window = WindowDetector()
        self.formations = FormationManager(config.formation_dir)
        self.gui = None
        self.running = False
        self.consecutive_misses = 0

        self._setup_logging()
        self._resolve_image_paths()
        pyautogui.FAILSAFE = config.failsafe

        if not HAS_OPENCV:
            self.log.warning(
                "opencv-python not installed — confidence matching disabled. "
                "Install with: pip install opencv-python"
            )

    def _setup_logging(self):
        self.log = logging.getLogger("IdleChampions")
        self.log.setLevel(logging.INFO)
        self.log.handlers.clear()

        fmt = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S"
        )
        console = logging.StreamHandler()
        console.setFormatter(fmt)
        self.log.addHandler(console)

        if self.config.log_to_file:
            log_dir = Path(self.config.log_dir)
            log_dir.mkdir(parents=True, exist_ok=True)
            ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            file_fmt = logging.Formatter(
                "%(asctime)s [%(levelname)s] %(message)s"
            )
            fh = logging.FileHandler(log_dir / f"session_{ts}.log")
            fh.setFormatter(file_fmt)
            self.log.addHandler(fh)

    def _resolve_image_paths(self):
        """Build full paths using resolution subfolder, with fallbacks."""
        base = Path(self.config.image_dir)
        candidates = [
            base / self.config.resolution,  # e.g. images/1280x720/
            base,                           # e.g. images/
            Path("."),                      # legacy flat layout
        ]
        res_dir = next((p for p in candidates if p.exists()), base)
        self.log.info("Image directory: %s", res_dir)

        self.image_categories = {
            category: [
                (name, str(res_dir / filename)) for name, filename in images
            ]
            for category, images in IMAGE_CATEGORIES.items()
        }

    def find_and_click(self, name, image_file):
        """Locate image on screen and click it. Returns True if found."""
        kwargs = {
            "grayscale": self.config.use_grayscale,
            "region": self.window.region,
        }
        if HAS_OPENCV:
            kwargs["confidence"] = self.config.confidence

        try:
            location = pyautogui.locateOnScreen(image_file, **kwargs)
        except pyautogui.ImageNotFoundException:
            return False
        except FileNotFoundError:
            self.log.warning("Image file missing: %s", image_file)
            return False
        except Exception as exc:
            self.log.debug("Error searching for %s: %s", name, exc)
            return False

        if location is None:
            return False

        center = pyautogui.center(location)

        if self.config.dry_run:
            self.log.info("[DRY] Found %-20s at (%d, %d)",
                          name, center.x, center.y)
        else:
            self.log.info("Found %-20s at (%d, %d) — click",
                          name, center.x, center.y)
            pyautogui.click(center.x, center.y)

        time.sleep(self.config.click_hold_time)
        self.stats.record_click(name)
        return True

    def click_with_retry(self, name, image_file):
        """Click an image, re-clicking until it's gone (for repeatable upgrades)."""
        found_once = False
        for _ in range(self.config.max_retries):
            if not self.find_and_click(name, image_file):
                break
            found_once = True
            time.sleep(self.config.search_delay)
        return found_once

    def click_category(self, category):
        """Click all images in a category."""
        found_any = False
        for name, image_file in self.image_categories.get(category, []):
            if self.click_with_retry(name, image_file):
                found_any = True
            time.sleep(self.config.search_delay)
        return found_any

    def run_cycle(self):
        """Run one scan cycle in priority order."""
        self.log.info("--- Cycle %d ---", self.stats.cycles + 1)

        # Refresh game window position each cycle
        self.window.find_game_window()

        found_any = False
        for category in self.config.priority_order:
            if self.click_category(category):
                found_any = True

        if found_any:
            self.consecutive_misses = 0
        else:
            self.consecutive_misses += 1
            self.stats.record_miss()
            if self.consecutive_misses >= self.config.stuck_threshold:
                self.log.warning(
                    "Nothing found for %d cycles — bot may be stuck!",
                    self.consecutive_misses,
                )
                self.notifier.notify(
                    "Idle Champions Bot — Stuck",
                    f"No elements detected for {self.consecutive_misses} "
                    "cycles. Check the game window.",
                )
                self.consecutive_misses = 0  # reset to avoid spam

        self.stats.record_cycle()

    def check_schedule(self):
        """Return False if scheduled runtime has elapsed."""
        if self.config.schedule_hours <= 0:
            return True
        elapsed_hours = self.stats.runtime.total_seconds() / 3600
        return elapsed_hours < self.config.schedule_hours

    def stop(self):
        self.running = False

    def run(self):
        self.running = True

        self.log.info("Idle Champions bot started")
        self.log.info(
            "  Confidence: %.0f%% | Grayscale: %s | Dry run: %s",
            self.config.confidence * 100,
            self.config.use_grayscale,
            self.config.dry_run,
        )
        if self.config.schedule_hours > 0:
            self.log.info("  Scheduled for %.1f hours",
                          self.config.schedule_hours)
        self.log.info("  Press Ctrl+C to stop")

        if self.config.enable_gui and HAS_TKINTER:
            self.gui = GUIOverlay(self.stats)
            self.gui.start(stop_callback=self.stop)

        self.notifier.notify("Idle Champions Bot", "Bot started!")

        try:
            while self.running and self.check_schedule():
                self.run_cycle()
                time.sleep(self.config.cycle_delay)
        except KeyboardInterrupt:
            self.log.info("Interrupted by user")

        self.log.info("Bot stopped")
        self.log.info("\n%s", self.stats.summary())
        self.notifier.notify(
            "Idle Champions Bot",
            f"Stopped. {self.stats.cycles} cycles, "
            f"{self.stats.total_found} clicks.",
        )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args():
    p = argparse.ArgumentParser(
        description="Idle Champions of the Forgotten Realms — Automation Bot",
    )
    p.add_argument("--config", type=str, default="config.json",
                   help="Path to config file (default: config.json)")
    p.add_argument("--confidence", type=float,
                   help="Image match confidence 0.0-1.0 (default: 0.7)")
    p.add_argument("--dry-run", action="store_true",
                   help="Scan and report without clicking")
    p.add_argument("--no-gui", action="store_true",
                   help="Disable the GUI overlay")
    p.add_argument("--no-notify", action="store_true",
                   help="Disable desktop notifications")
    p.add_argument("--no-log-file", action="store_true",
                   help="Disable logging to file")
    p.add_argument("--schedule", type=float, dest="schedule_hours",
                   help="Run for N hours then stop (default: forever)")
    p.add_argument("--resolution", type=str,
                   help="Image set resolution (default: 1280x720)")
    p.add_argument("--retries", type=int, dest="max_retries",
                   help="Max click retries per image")
    p.add_argument("--save-formation", type=str, metavar="NAME",
                   help="Create a new formation stub with given name")
    p.add_argument("--list-formations", action="store_true",
                   help="List saved formations and exit")
    return p.parse_args()


def build_overrides(args):
    overrides = {}
    if args.confidence is not None:
        overrides["confidence"] = args.confidence
    if args.dry_run:
        overrides["dry_run"] = True
    if args.no_gui:
        overrides["enable_gui"] = False
    if args.no_notify:
        overrides["enable_notifications"] = False
    if args.no_log_file:
        overrides["log_to_file"] = False
    if args.schedule_hours is not None:
        overrides["schedule_hours"] = args.schedule_hours
    if args.resolution:
        overrides["resolution"] = args.resolution
    if args.max_retries is not None:
        overrides["max_retries"] = args.max_retries
    return overrides


def main():
    args = parse_args()
    config = Config(args.config)
    config.apply_overrides(build_overrides(args))

    # Formation subcommands
    if args.list_formations:
        fm = FormationManager(config.formation_dir)
        formations = fm.list_formations()
        if formations:
            print("Saved formations:")
            for name in formations:
                print(f"  - {name}")
        else:
            print("No saved formations.")
        return

    if args.save_formation:
        fm = FormationManager(config.formation_dir)
        path = fm.save(args.save_formation, {
            "name": args.save_formation,
            "created": datetime.datetime.now().isoformat(),
            "champions": [],
            "notes": "Edit this file to define champion slot positions.",
        })
        print(f"Formation stub saved: {path}")
        return

    bot = IdleChampionsBot(config)
    bot.run()


if __name__ == "__main__":
    main()
