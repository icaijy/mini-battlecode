"""User-facing workflow smoke tests (no network required)."""
import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from arena import cli

ROOT = Path(__file__).resolve().parents[1]


class CLITest(unittest.TestCase):
    def test_doctor(self):
        with contextlib.redirect_stdout(io.StringIO()) as output:
            cli.main(["doctor", "--season", "courier_s1"])
        self.assertIn("Ready.", output.getvalue())

    def test_new_season_draft(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(cli, "ROOT", Path(folder)):
            with contextlib.redirect_stdout(io.StringIO()):
                cli.main(["new-season", "testing_season"])
            draft = Path(folder) / "seasons" / "testing_season"
            manifest = json.loads((draft / "manifest.json").read_text())
            self.assertEqual(manifest["id"], "testing_season")
            self.assertIn("DRAFT", manifest["title"])
            self.assertTrue((draft / "game.py").exists())
            self.assertTrue((draft / "viewer.html").exists())

    def test_finals_full_workflow(self):
        src = ROOT / "seasons" / "courier_s1" / "example_bot.cpp"
        with tempfile.TemporaryDirectory() as folder:
            result = Path(folder) / "results"
            published = Path(folder) / "site"
            with contextlib.redirect_stdout(io.StringIO()):
                cli.main(["finals", "--season", "courier_s1",
                          "--bot", f"human={src}", "--bot", f"ai={src}",
                          "--human", "human", "--seed-count", "2",
                          "--out", str(result), "--site-root", str(published)])
            payload = json.loads((result / "tournament.json").read_text())
            self.assertEqual(payload["matches_total"], 4)
            self.assertTrue((published / "index.html").is_file())
            self.assertTrue((published / "courier_s1" / "viewer.html").is_file())
            self.assertTrue((published / "courier_s1" / "matches.json").is_file())


if __name__ == "__main__":
    unittest.main()
