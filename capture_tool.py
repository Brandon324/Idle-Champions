"""
Screenshot Capture Tool for Idle Champions Bot

Lets you click-and-drag to select a region of the screen and saves it as
a PNG file for use with the bot's image recognition.

Usage:
    python capture_tool.py
    python capture_tool.py --output-dir images/1920x1080
"""

import argparse
import sys
import time
from pathlib import Path

try:
    import pyautogui
    import tkinter as tk
except ImportError as e:
    print(f"Missing dependency: {e}")
    print("Install with: pip install -r requirements.txt")
    sys.exit(1)


class RegionSelector:
    """Full-screen translucent overlay for selecting a screen region."""

    def __init__(self):
        self.start_x = 0
        self.start_y = 0
        self.end_x = 0
        self.end_y = 0
        self.rect = None
        self.selected = False
        self.root = None
        self.canvas = None

    def select(self):
        """Show overlay and let the user drag to select a region."""
        self.root = tk.Tk()
        self.root.attributes("-fullscreen", True)
        self.root.attributes("-alpha", 0.3)
        self.root.attributes("-topmost", True)
        self.root.configure(bg="black")

        self.canvas = tk.Canvas(
            self.root, cursor="crosshair", bg="black", highlightthickness=0
        )
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self.canvas.create_text(
            self.root.winfo_screenwidth() // 2, 30,
            text="Click and drag to select a region. ESC to cancel.",
            fill="white", font=("Arial", 16),
        )

        self.canvas.bind("<ButtonPress-1>", self._on_press)
        self.canvas.bind("<B1-Motion>", self._on_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_release)
        self.root.bind("<Escape>", lambda e: self.root.destroy())

        self.root.mainloop()

        if self.selected:
            x1 = min(self.start_x, self.end_x)
            y1 = min(self.start_y, self.end_y)
            x2 = max(self.start_x, self.end_x)
            y2 = max(self.start_y, self.end_y)
            return (x1, y1, x2, y2)
        return None

    def _on_press(self, event):
        self.start_x = event.x
        self.start_y = event.y
        if self.rect:
            self.canvas.delete(self.rect)
        self.rect = self.canvas.create_rectangle(
            event.x, event.y, event.x, event.y, outline="lime", width=2
        )

    def _on_drag(self, event):
        self.canvas.coords(
            self.rect, self.start_x, self.start_y, event.x, event.y
        )

    def _on_release(self, event):
        self.end_x = event.x
        self.end_y = event.y
        self.selected = True
        self.root.destroy()


def capture_region(region, output_path):
    """Take a screenshot and crop to the selected region."""
    time.sleep(0.5)  # let the overlay close
    screenshot = pyautogui.screenshot()
    x1, y1, x2, y2 = region
    cropped = screenshot.crop((x1, y1, x2, y2))
    cropped.save(output_path)
    return output_path


def main():
    parser = argparse.ArgumentParser(
        description="Capture screen regions for bot image recognition"
    )
    parser.add_argument(
        "--output-dir", type=str, default="images/1280x720",
        help="Directory to save captured images (default: images/1280x720)",
    )
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 50)
    print("  Idle Champions — Screenshot Capture Tool")
    print("=" * 50)
    print(f"Saving to: {output_dir}/")

    while True:
        name = input(
            "\nImage name (e.g. BlueCoin) or 'quit' to exit: "
        ).strip()
        if name.lower() in ("quit", "q", "exit"):
            break
        if not name:
            print("Name cannot be empty.")
            continue

        output_path = output_dir / f"{name}.PNG"
        print(f"Selecting region for '{name}'...")
        print("Dark overlay will appear. Click + drag, or ESC to cancel.")
        time.sleep(1)

        region = RegionSelector().select()
        if region is None:
            print("Selection cancelled.")
            continue

        x1, y1, x2, y2 = region
        w, h = x2 - x1, y2 - y1
        if w < 5 or h < 5:
            print("Selection too small, try again.")
            continue

        capture_region(region, output_path)
        print(f"Saved: {output_path} ({w}x{h} pixels)")

    print("\nDone.")


if __name__ == "__main__":
    main()
