import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from arena.core import resolve_season, create_game, compile_cpp, run_match, BotFault
from arena.publish import publish, publish_hub
from arena.tournament import run_tournament

ROOT = Path(__file__).resolve().parents[1]


class FrameworkTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.info = resolve_season("courier_s1")
        cls.work = tempfile.TemporaryDirectory(prefix="mini-battlecode-test-")
        cls.root = Path(cls.work.name)
        cls.bin = cls.root / "idle"
        compile_cpp(cls.info.example, cls.info, cls.bin)

    @classmethod
    def tearDownClass(cls):
        cls.work.cleanup()

    def test_game_plugin_and_perspective(self):
        game = create_game(self.info, 7)
        self.assertEqual(game.turn, 0)
        self.assertEqual(game.max_turns, 140)
        self.assertEqual(len(game.snapshot()["wells"]), 7)
        self.assertTrue(game.observe(0).startswith("TURN 0"))
        self.assertTrue(game.observe(1).startswith("TURN 0"))
        self.assertEqual(game.parse_action(0, "0 1 2 3"), [0, 1, 2, 3])
        with self.assertRaises(ValueError):
            game.parse_action(0, "1 2 3 9")

    def test_match_and_replay(self):
        replay = self.root / "solo.json"
        p = [{"id": "a", "binary": str(self.bin)}, {"id": "b", "binary": str(self.bin)}]
        match = run_match(self.info, p, seed=2, replay=replay)
        self.assertEqual(match["scores"], [0, 0])
        self.assertIsNone(match["winner"])
        self.assertFalse(match["errors"])
        self.assertEqual(match["turns_played"], 140)
        data = json.loads(replay.read_text())
        self.assertEqual(len(data["frames"]), 141)
        self.assertEqual(data["result"]["bot_ids"], ["a", "b"])

    def test_forfeit_invalid_output(self):
        src = self.root / "bad.cpp"
        src.write_text("""#include "arena.hpp"
#include <iostream>
using namespace courier;
void courier::tick(const State&) { std::cout << "invalid" << std::endl; }
""")
        bad = self.root / "bad"
        compile_cpp(src, self.info, bad)
        p = [{"id": "bad", "binary": str(bad)}, {"id": "good", "binary": str(self.bin)}]
        match = run_match(self.info, p, 1)
        self.assertEqual(match["winner"], 1)
        self.assertEqual(match["turns_played"], 0)
        self.assertEqual(len(match["errors"]), 1)

    def test_timeout_forfeits(self):
        src = self.root / "spin.cpp"
        src.write_text("""#include "arena.hpp"
using namespace courier;
void courier::tick(const State&) { volatile int counter=0; while(true) ++counter; }
""")
        binary = self.root / "spin"
        compile_cpp(src, self.info, binary)
        p = [{"id": "spin", "binary": str(binary)},
             {"id": "idle", "binary": str(self.bin)}]
        result = run_match(self.info, p, seed=1, timeout=0.04)
        self.assertEqual(result["winner"], 1)
        self.assertIn("exceeded", result["errors"][0]["reason"])

    def test_round_robin_and_publish(self):
        src1 = self.root / "one.cpp"
        src2 = self.root / "two.cc"
        code = self.info.example.read_text(encoding="utf-8")
        src1.write_text(code)
        src2.write_text(code)
        roster = self.root / "roster.json"
        roster.write_text(json.dumps({"season": "courier_s1", "seeds": [3, 5],
            "bots": [{"id": "human", "source": "one.cpp", "kind": "human"},
                     {"id": "alpha", "source": "two.cc", "kind": "ai"}]}))
        out = self.root / "tournament"
        report = run_tournament(self.info, roster, out, features=3, verbose=False)
        self.assertEqual(len(report["matches"]), 4)  # 2 seeds × both sides
        self.assertEqual(len(report["leaderboard"]), 2)
        self.assertTrue(all(s["games"] == 4 for s in report["leaderboard"]))
        self.assertTrue(all(s["match_points"] == 2 for s in report["leaderboard"]))
        self.assertGreater(len(report["featured"]), 0)
        dest = self.root / "published"
        publish(self.info, out / "tournament.json", dest)
        self.assertTrue((dest / "index.html").is_file())
        self.assertTrue((dest / "viewer.html").is_file())
        self.assertTrue((dest / "results.json").is_file())
        self.assertEqual(len(json.loads((dest / "matches.json").read_text())), 4)
        self.assertTrue(list((dest / "replays").glob("*.json")))
        publish_hub(self.root)
        hub = json.loads((self.root / "seasons.json").read_text())
        self.assertTrue(any(s["season"] == "published" for s in hub["seasons"]))


if __name__ == "__main__":
    unittest.main()
