# Idle Champions Automation Bot

A feature-rich Python bot that automates **Idle Champions of the Forgotten Realms**. It continuously scans the screen for coins, upgrades, and UI buttons, clicking them automatically so you can idle hands-free.

## Features

- **Reliable image matching** — confidence threshold + grayscale matching so it works across resolutions and game updates
- **Game window auto-detection** — finds the Idle Champions window and only scans that area (faster, fewer false positives)
- **Region-limited scanning** — scans only the game window instead of the whole screen
- **Priority click order** — time-sensitive buttons (Complete, Skip, Continue) are checked first
- **Retry logic** — re-clicks repeatable elements like upgrade buttons until they're done
- **Stuck detection** — alerts you if nothing has been found for N cycles
- **Dry-run mode** — scan and report without clicking, perfect for testing
- **Scheduling** — run for N hours then auto-stop
- **Live GUI overlay** — always-on-top window with stats and a stop button
- **Session stats** — tracks runtime, cycles, clicks per element
- **Desktop notifications** — alerts on start, stop, and stuck states
- **File logging** — every session saved to `logs/` with timestamps
- **Configuration file** — all settings live in `config.json`
- **CLI arguments** — override any setting on the command line
- **Multi-resolution support** — drop image sets in `images/<resolution>/`
- **Formation save/load** — JSON-based champion formation storage
- **Screenshot capture tool** — `capture_tool.py` for easily updating image references
- **Adventure auto-restart** — priority order ensures Complete/Continue are clicked first
- **Graceful degradation** — optional dependencies (notifications, GUI, window detection) all degrade safely

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Launch Idle Champions in 1280x720

# 3. Run the bot
python idle_champions.py
```

Press **Ctrl+C** or click **Stop Bot** in the overlay to stop.

## Project Structure

```
Idle-Champions/
├── idle_champions.py        # Main bot
├── capture_tool.py          # Screenshot helper for new image sets
├── config.json              # All bot settings
├── requirements.txt         # Python dependencies
├── README.md
├── .gitignore
├── images/
│   └── 1280x720/            # PNG references for default resolution
├── logs/                    # Session log files (gitignored)
└── formations/              # Saved champion formations (gitignored)
```

## CLI Usage

```bash
python idle_champions.py                      # Default run with config.json
python idle_champions.py --dry-run            # Scan & report, no clicks
python idle_champions.py --schedule 4         # Auto-stop after 4 hours
python idle_champions.py --confidence 0.6     # Lower match threshold
python idle_champions.py --resolution 1920x1080  # Use a different image set
python idle_champions.py --no-gui --no-notify    # Headless mode
python idle_champions.py --list-formations
python idle_champions.py --save-formation MyTeam
```

Run `python idle_champions.py --help` for the full list.

## Configuration (`config.json`)

| Setting | Default | Description |
|---|---|---|
| `confidence` | `0.7` | Image match threshold (0.0–1.0). Lower = more forgiving |
| `use_grayscale` | `true` | Match in grayscale for speed/reliability |
| `click_hold_time` | `0.3` | Seconds to pause after each click |
| `cycle_delay` | `2.0` | Seconds between full scan cycles |
| `search_delay` | `0.3` | Seconds between individual image searches |
| `failsafe` | `false` | If true, moving mouse to corner aborts the bot |
| `resolution` | `"1280x720"` | Image set subfolder under `images/` |
| `image_dir` | `"images"` | Root images directory |
| `log_dir` | `"logs"` | Where session logs are written |
| `formation_dir` | `"formations"` | Where formation JSONs are stored |
| `dry_run` | `false` | Scan and log without clicking |
| `max_retries` | `3` | Re-click attempts for repeatable buttons |
| `stuck_threshold` | `10` | Cycles with zero hits before alerting |
| `schedule_hours` | `0` | Auto-stop after N hours (0 = forever) |
| `priority_order` | `["complete", "skip", ...]` | Category scan order |
| `enable_notifications` | `true` | Desktop notifications |
| `enable_gui` | `true` | Live GUI overlay window |
| `log_to_file` | `true` | Write session logs to `logs/` |
| `auto_restart_adventure` | `true` | Reserved for adventure-restart logic |

## Adding a New Resolution

1. Run the capture tool pointed at a new resolution folder:

   ```bash
   python capture_tool.py --output-dir images/1920x1080
   ```

2. Click and drag to capture each UI element, naming each one (e.g. `BlueCoin`, `CompleteButton`). Use the same names as the existing PNGs in `images/1280x720/`.

3. Run the bot with the new resolution:

   ```bash
   python idle_champions.py --resolution 1920x1080
   ```

## Updating Existing Screenshots

If the game changes a button's appearance and the bot stops finding it:

1. `python capture_tool.py`
2. Re-capture only the broken element with the same name
3. If matches are still flaky, lower `confidence` to `0.6` in `config.json`

## Formations

Save a formation stub:

```bash
python idle_champions.py --save-formation MyTeam
```

This creates `formations/MyTeam.json` which you can edit to define champion slot positions. List formations with `--list-formations`.

## Optional Dependencies

The bot degrades gracefully if any of these are missing:

| Package | Used For |
|---|---|
| `opencv-python` | Confidence + grayscale matching (highly recommended) |
| `pygetwindow` | Game window auto-detection |
| `plyer` | Desktop notifications |
| `tkinter` | GUI overlay (built into most Python installs) |

## Stopping the Bot

- **Ctrl+C** in the terminal
- Click **Stop Bot** in the overlay window
- Move mouse to a screen corner (only if `failsafe` is enabled)
