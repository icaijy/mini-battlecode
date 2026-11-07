"""External ZIP -> build -> duel -> paired finals -> database archive."""
from __future__ import annotations
import contextlib
import io
import json
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

from arena import cli
from arena.archive import contestant_kit, season_package
from arena.core import open_season, SeasonError
from tests.fixture import make_fixture

class CLIWorkflow(unittest.TestCase):
    def test_doctor_without_game(self):
        with contextlib.redirect_stdout(io.StringIO()) as buff:
            cli.main(['doctor'])
        self.assertIn('Ready.', buff.getvalue())

    def test_external_zip_and_final(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            folder = make_fixture(root)
            plugin = root / 'season.zip'
            with open_season(folder) as info:
                season_package(info, plugin)
            with open_season(plugin) as info:
                self.assertEqual(info.id, 'synthetic_test')
                kit = root / 'kit.zip'
                contestant_kit(info, kit)
                with zipfile.ZipFile(kit) as z:
                    self.assertIn('arena.hpp', z.namelist())
                    self.assertIn('game.py', z.namelist())
                    self.assertIn('manifest.json', z.namelist())
            outfile = root / 'results'
            archive = root / 'database.zip'
            src = folder / 'example_bot.cpp'
            with contextlib.redirect_stdout(io.StringIO()):
                cli.main(['finals','--season',str(plugin),
                          '--bot',f'human={src}', '--bot',f'ai={src}',
                          '--human','human', '--seed-count','2',
                          '--out',str(outfile), '--archive',str(archive)])
            result = json.loads((outfile/'tournament.json').read_text())
            self.assertEqual(result['matches_total'], 4)
            with zipfile.ZipFile(archive) as z:
                names = z.namelist()
                self.assertIn('tournament.json', names)
                self.assertIn('season/game.py', names)
                self.assertIn('season/viewer.html', names)
                self.assertIn('sources/human.cpp', names)
                self.assertEqual(len([n for n in names if n.startswith('replays/')]), 4)
                self.assertEqual(json.loads(z.read('tournament.json'))['season'], 'synthetic_test')

    def test_traversal_zip_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'evil.zip'
            with zipfile.ZipFile(path,'w') as z:
                z.writestr('../../tmp/escape','x')
            with self.assertRaises(SeasonError):
                with open_season(path):
                    pass

if __name__ == '__main__':
    unittest.main()
