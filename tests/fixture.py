"""Generate a disposable *synthetic* game for core tests; no seasons in repository."""
from pathlib import Path
import json

GAME = '''class TestGame:
    max_turns = 4
    def __init__(self, seed):
        self.seed = seed
        self.turn = 0
        self.scores = [0, 0]
    def observe(self, side):
        return f"TICK {self.turn}\\n"
    def parse_action(self, side, text):
        if text not in ("0", "1"):
            raise ValueError("Bad action")
        return int(text)
    def step(self, actions):
        self.scores[0] += actions[0]
        self.scores[1] += actions[1]
        self.turn += 1
    def snapshot(self):
        return {"tick": self.turn, "scores": list(self.scores)}
    def outcome(self):
        a, b = self.scores
        return {"scores": list(self.scores), "winner": 0 if a > b else 1 if b > a else None}

def create_game(seed):
    return TestGame(seed)
'''
HEADER = '''#pragma once
namespace toy {
struct State { int turn = 0; };
void tick(const State& s);
void action(int v);
} // namespace toy
'''
ADAPTER = '''#include "arena.hpp"
#include <iostream>
#include <string>
using namespace toy;
static int value = 0;
void toy::action(int v) { value = v; }
int main(){
  std::string cmd;
  while(std::cin >> cmd){
    if(cmd == "END") break;
    int t;
    if(cmd != "TICK" || !(std::cin >> t)) break;
    value = 0;
    tick(State{t});
    std::cout << value << std::endl;
  }
}
'''
BOT = '''#include "arena.hpp"
using namespace toy;
void toy::tick(const State&) { action(1); }
'''
VIEWER = '''<!doctype html><html><body><h1>Synthetic test</h1><script>
window.addEventListener('message', e=>{if(e.data?.type==='mini-battlecode-replay')
 document.body.dataset.loaded=String(e.data.replay.frames.length)})
</script></body></html>'''


def make_fixture(root: Path):
    folder = root / 'external_game'
    folder.mkdir(exist_ok=True)
    files = {'game.py': GAME, 'arena.hpp': HEADER, 'grader.cpp': ADAPTER,
             'example_bot.cpp': BOT, 'viewer.html': VIEWER,
             'RULES.md': '# Synthetic test\n\n仅用于内部测试。'}
    for name, content in files.items():
        (folder / name).write_text(content, encoding='utf-8')
    (folder / 'manifest.json').write_text(json.dumps({
        'id':'synthetic_test', 'title':'Synthetic Test', 'version':'1.0',
        'judge':'game.py', 'header':'arena.hpp', 'adapter':'grader.cpp',
        'example':'example_bot.cpp', 'viewer':'viewer.html',
        'rules':'RULES.md', 'default_seeds':2
    }), encoding='utf-8')
    return folder
