"""
Unit tests for the Idle Champions automation bot.

Tests pure logic only — does not exercise pyautogui screen functions,
GUI overlay, or notification system (those require a display + game).

Run with:
    python -m unittest tests.py
    python tests.py
"""

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

# Stub out pyautogui before importing the bot module so we can run
# these tests in headless environments.
sys.modules.setdefault("pyautogui", type(sys)("pyautogui"))
sys.modules["pyautogui"].FAILSAFE = False

import idle_champions as ic  # noqa: E402


class TestConfig(unittest.TestCase):
    def test_defaults_are_loaded(self):
        with tempfile.TemporaryDirectory() as tmp:
            cfg = ic.Config(os.path.join(tmp, "missing.json"))
        self.assertEqual(cfg.confidence, 0.7)
        self.assertTrue(cfg.use_grayscale)
        self.assertFalse(cfg.dry_run)
        self.assertEqual(cfg.resolution, "1280x720")
        self.assertEqual(
            cfg.priority_order,
            ["complete", "skip", "continue", "coins", "upgrades", "ui"],
        )

    def test_loads_overrides_from_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "config.json"
            path.write_text(json.dumps({
                "confidence": 0.55,
                "schedule_hours": 2,
            }))
            cfg = ic.Config(str(path))
        self.assertEqual(cfg.confidence, 0.55)
        self.assertEqual(cfg.schedule_hours, 2)
        # Other defaults should be unchanged
        self.assertTrue(cfg.use_grayscale)

    def test_apply_overrides_skips_none(self):
        with tempfile.TemporaryDirectory() as tmp:
            cfg = ic.Config(os.path.join(tmp, "missing.json"))
        cfg.apply_overrides({
            "confidence": 0.85,
            "use_grayscale": None,  # should be ignored
            "enable_gui": False,
        })
        self.assertEqual(cfg.confidence, 0.85)
        self.assertTrue(cfg.use_grayscale)  # unchanged
        self.assertFalse(cfg.enable_gui)

    def test_unknown_attribute_raises(self):
        with tempfile.TemporaryDirectory() as tmp:
            cfg = ic.Config(os.path.join(tmp, "missing.json"))
        with self.assertRaises(AttributeError):
            _ = cfg.nonexistent_setting

    def test_corrupt_config_falls_back_to_defaults(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "config.json"
            path.write_text("{not valid json")
            cfg = ic.Config(str(path))
        self.assertEqual(cfg.confidence, 0.7)


class TestStats(unittest.TestCase):
    def test_initial_state(self):
        stats = ic.Stats()
        self.assertEqual(stats.cycles, 0)
        self.assertEqual(stats.total_found, 0)
        self.assertEqual(stats.total_missed, 0)
        self.assertEqual(dict(stats.clicks), {})

    def test_record_click_increments_counts(self):
        stats = ic.Stats()
        stats.record_click("BlueCoin")
        stats.record_click("BlueCoin")
        stats.record_click("RedUpgrade")
        self.assertEqual(stats.clicks["BlueCoin"], 2)
        self.assertEqual(stats.clicks["RedUpgrade"], 1)
        self.assertEqual(stats.total_found, 3)

    def test_record_miss_and_cycle(self):
        stats = ic.Stats()
        stats.record_miss()
        stats.record_cycle()
        stats.record_cycle()
        self.assertEqual(stats.total_missed, 1)
        self.assertEqual(stats.cycles, 2)

    def test_summary_contains_top_clicks(self):
        stats = ic.Stats()
        stats.record_click("BlueCoin")
        stats.record_click("BlueCoin")
        stats.record_click("RedUpgrade")
        summary = stats.summary()
        self.assertIn("BlueCoin", summary)
        self.assertIn("RedUpgrade", summary)
        self.assertIn("Session Summary", summary)
        # BlueCoin (2) should appear before RedUpgrade (1)
        self.assertLess(summary.index("BlueCoin"), summary.index("RedUpgrade"))

    def test_summary_handles_no_clicks(self):
        stats = ic.Stats()
        summary = stats.summary()
        self.assertIn("(none)", summary)


class TestFormationManager(unittest.TestCase):
    def test_save_and_load_roundtrip(self):
        with tempfile.TemporaryDirectory() as tmp:
            fm = ic.FormationManager(tmp)
            data = {"name": "MyTeam", "champions": ["A", "B", "C"]}
            saved_path = fm.save("MyTeam", data)
            self.assertTrue(saved_path.exists())

            loaded = fm.load("MyTeam")
            self.assertEqual(loaded, data)

    def test_load_missing_returns_none(self):
        with tempfile.TemporaryDirectory() as tmp:
            fm = ic.FormationManager(tmp)
            self.assertIsNone(fm.load("nope"))

    def test_list_formations_sorted(self):
        with tempfile.TemporaryDirectory() as tmp:
            fm = ic.FormationManager(tmp)
            fm.save("Zebra", {})
            fm.save("Apple", {})
            fm.save("Mango", {})
            self.assertEqual(fm.list_formations(), ["Apple", "Mango", "Zebra"])

    def test_list_empty(self):
        with tempfile.TemporaryDirectory() as tmp:
            fm = ic.FormationManager(tmp)
            self.assertEqual(fm.list_formations(), [])


class TestImageCategories(unittest.TestCase):
    def test_all_categories_have_entries(self):
        for category, images in ic.IMAGE_CATEGORIES.items():
            self.assertTrue(images, f"Category '{category}' is empty")

    def test_entries_are_name_filename_tuples(self):
        for category, images in ic.IMAGE_CATEGORIES.items():
            for entry in images:
                self.assertEqual(len(entry), 2,
                                 f"Bad entry in {category}: {entry}")
                name, filename = entry
                self.assertIsInstance(name, str)
                self.assertIsInstance(filename, str)
                self.assertTrue(filename.endswith(".PNG"),
                                f"Filename should be .PNG: {filename}")

    def test_default_priority_order_covers_all_categories(self):
        cfg_categories = set(ic.Config.DEFAULTS["priority_order"])
        image_categories = set(ic.IMAGE_CATEGORIES.keys())
        self.assertEqual(cfg_categories, image_categories)

    def test_image_files_exist_for_default_resolution(self):
        base = Path("images/1280x720")
        if not base.exists():
            self.skipTest("Default image directory not present")
        for images in ic.IMAGE_CATEGORIES.values():
            for _, filename in images:
                path = base / filename
                self.assertTrue(path.exists(),
                                f"Missing image file: {path}")


class TestArgParse(unittest.TestCase):
    def test_default_args(self):
        args = ic.parse_args.__wrapped__() if hasattr(ic.parse_args, "__wrapped__") else None
        # parse_args reads sys.argv directly; test build_overrides instead
        class FakeArgs:
            confidence = None
            dry_run = False
            no_gui = False
            no_notify = False
            no_log_file = False
            schedule_hours = None
            resolution = None
            max_retries = None
        overrides = ic.build_overrides(FakeArgs())
        self.assertEqual(overrides, {})

    def test_dry_run_override(self):
        class FakeArgs:
            confidence = 0.5
            dry_run = True
            no_gui = True
            no_notify = False
            no_log_file = False
            schedule_hours = 3.0
            resolution = "1920x1080"
            max_retries = 5
        overrides = ic.build_overrides(FakeArgs())
        self.assertEqual(overrides["confidence"], 0.5)
        self.assertTrue(overrides["dry_run"])
        self.assertFalse(overrides["enable_gui"])
        self.assertEqual(overrides["schedule_hours"], 3.0)
        self.assertEqual(overrides["resolution"], "1920x1080")
        self.assertEqual(overrides["max_retries"], 5)


if __name__ == "__main__":
    unittest.main(verbosity=2)
