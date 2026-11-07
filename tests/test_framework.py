"""Generic judge tests use an on-the-fly synthetic plugin, never a real season."""
import json
import tempfile
import unittest
from pathlib import Path
from arena.core import resolve_season, create_game, compile_cpp, run_match
from arena.tournament import run_tournament
from tests.fixture import make_fixture

class FrameworkTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.work = tempfile.TemporaryDirectory(prefix='mbc-test-')
        cls.root = Path(cls.work.name)
        cls.info = resolve_season(make_fixture(cls.root))
        cls.binary = cls.root/'example'
        compile_cpp(cls.info.example, cls.info, cls.binary)

    @classmethod
    def tearDownClass(cls): cls.work.cleanup()

    def test_judge_and_replay(self):
        game = create_game(self.info, 3)
        self.assertEqual(game.max_turns, 4)
        self.assertEqual(game.parse_action(0, '1'), 1)
        with self.assertRaises(ValueError): game.parse_action(0, '2')
        replay = self.root/'replay.json'
        players=[{'id':'a','binary':str(self.binary)}, {'id':'b','binary':str(self.binary)}]
        match=run_match(self.info,players,7,replay=replay)
        self.assertEqual(match['scores'],[4,4])
        self.assertIsNone(match['winner'])
        self.assertEqual(len(json.loads(replay.read_text())['frames']),5)

    def test_round_robin(self):
        roster=self.root/'roster.json'
        roster.write_text(json.dumps({'season':self.info.id,'seeds':[1,2],
            'bots':[{'id':'one','source':str(self.info.example),'kind':'human'},
                    {'id':'two','source':str(self.info.example),'kind':'ai'}]}))
        report=run_tournament(self.info,roster,self.root/'rr',verbose=False)
        self.assertEqual(report['matches_total'],4)
        self.assertEqual(len(list((self.root/'rr'/'replays').glob('*.json'))),4)
        self.assertEqual(report['leaderboard'][0]['match_points'],2)

if __name__=='__main__': unittest.main()
