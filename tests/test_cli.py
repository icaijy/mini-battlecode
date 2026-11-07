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
from arena.core import open_season, SeasonError, resolve_season
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
            with zipfile.ZipFile(plugin) as z:
                for name in ('RULES.md', 'INTERFACE.md', 'AI_PROMPT.md'):
                    self.assertIn(name, z.namelist())
            with open_season(plugin) as info:
                self.assertEqual(info.id, 'synthetic_test')
                kit = root / 'kit.zip'
                contestant_kit(info, kit)
                with zipfile.ZipFile(kit) as z:
                    self.assertIn('arena.hpp', z.namelist())
                    self.assertIn('game.py', z.namelist())
                    self.assertIn('manifest.json', z.namelist())
                    for name in ('RULES.md', 'INTERFACE.md', 'AI_PROMPT.md'):
                        self.assertIn(name, z.namelist())
                        self.assertIn('## 中文', z.read(name).decode('utf-8'))
                        self.assertIn('## English', z.read(name).decode('utf-8'))
                # Legacy "kit" command must produce exactly the same public
                # package: no secret organiser/contestant variants.
                with zipfile.ZipFile(plugin) as original:
                    with zipfile.ZipFile(kit) as copy:
                        self.assertEqual(sorted(original.namelist()), sorted(copy.namelist()))
                        for filename in original.namelist():
                            self.assertEqual(original.read(filename), copy.read(filename))
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
                for name in ('RULES.md', 'INTERFACE.md', 'AI_PROMPT.md'):
                    self.assertIn('season/' + name, names)
                self.assertIn('sources/human.cpp', names)
                self.assertEqual(len([n for n in names if n.startswith('replays/')]), 4)
                self.assertEqual(json.loads(z.read('tournament.json'))['season'], 'synthetic_test')

    def test_finals_discovers_every_cpp_cc_and_reports_wins(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            season = make_fixture(root)
            bots = root / 'all_bots'
            bots.mkdir()
            example = (season / 'example_bot.cpp').read_text(encoding='utf-8')
            (bots / 'Human.cpp').write_text(example, encoding='utf-8')
            (bots / 'GPT.cc').write_text(example, encoding='utf-8')
            (bots / 'README.txt').write_text('not a bot', encoding='utf-8')
            out = root / 'results'
            with contextlib.redirect_stdout(io.StringIO()) as capture:
                cli.main(['finals', '--season', str(season),
                          '--bots-dir', str(bots), '--seed-count', '1',
                          '--out', str(out)])
            stdout = capture.getvalue()
            self.assertIn('Human.cpp', stdout)
            self.assertIn('GPT.cc', stdout)
            self.assertIn('Wins  Draws  Losses', stdout)
            self.assertNotIn('README.txt', stdout)
            self.assertNotIn('[1/2]', stdout)  # no per-match spam
            report = json.loads((out / 'tournament.json').read_text())
            self.assertEqual(report['matches_total'], 2)
            self.assertEqual({b['label'] for b in report['leaderboard']},
                             {'Human.cpp', 'GPT.cc'})
            self.assertTrue(all(b['wins'] == 0 and b['draws'] == 2
                                for b in report['leaderboard']))
            self.assertTrue((out / 'database_import.zip').is_file())
            self.assertNotIn('featured', report)

    def test_finals_folder_requires_two_cpp_files(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            season = make_fixture(root)
            bots = root / 'bots'
            bots.mkdir()
            (bots / 'readme.txt').write_text('not a bot', encoding='utf-8')
            with self.assertRaises(SystemExit):
                with contextlib.redirect_stderr(io.StringIO()):
                    cli.main(['finals', '--season', str(season),
                              '--bots-dir', str(bots), '--out', str(root / 'out')])

    def test_v2_rejects_missing_document(self):
        with tempfile.TemporaryDirectory() as d:
            folder = make_fixture(Path(d))
            (folder / 'AI_PROMPT.md').unlink()
            with self.assertRaisesRegex(SeasonError, 'Missing season file'):
                resolve_season(folder)

    def test_v2_accepts_document_layouts_without_exact_language_headings(self):
        layouts = (
            '# API / 接口\n中文说明。\nEnglish instructions.\n',
            '### 中文说明\n测试。\n### English guide\nTest.\n',
            '## English\nImplement tick().\n',
        )
        for text in layouts:
            with self.subTest(text=text), tempfile.TemporaryDirectory() as d:
                folder = make_fixture(Path(d))
                for name in ('RULES.md', 'INTERFACE.md', 'AI_PROMPT.md'):
                    (folder / name).write_text(text, encoding='utf-8')
                self.assertEqual(resolve_season(folder).id, 'synthetic_test')
                plugin = Path(d) / 'season.zip'
                with open_season(folder) as info:
                    season_package(info, plugin)
                with open_season(plugin) as info:
                    for name in ('rules', 'interface', 'ai_prompt'):
                        self.assertEqual(getattr(info, name).read_text(encoding='utf-8'), text)

    def test_v2_rejects_empty_documents(self):
        for name in ('RULES.md', 'INTERFACE.md', 'AI_PROMPT.md'):
            for text in ('', ' \n\t'):
                with self.subTest(name=name, text=text), tempfile.TemporaryDirectory() as d:
                    folder = make_fixture(Path(d))
                    (folder / name).write_text(text, encoding='utf-8')
                    with self.assertRaisesRegex(SeasonError, name + ' must not be empty'):
                        resolve_season(folder)

    def test_v1_legacy_zip_still_supported(self):
        with tempfile.TemporaryDirectory() as d:
            folder = make_fixture(Path(d))
            manifest_path = folder / 'manifest.json'
            manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
            for name in ('format_version', 'interface', 'ai_prompt'):
                manifest.pop(name)
            manifest_path.write_text(json.dumps(manifest), encoding='utf-8')
            with open_season(folder) as info:
                self.assertIsNone(info.interface)
                self.assertIsNone(info.ai_prompt)
                old = Path(d) / 'legacy.zip'
                season_package(info, old)
            with open_season(old) as info:
                self.assertEqual(info.id, 'synthetic_test')

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
