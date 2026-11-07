"""Courier Clash S1 rules. No match management lives in this module."""
from __future__ import annotations

import random
from dataclasses import dataclass

N, DRONES, WELLS, MAX_CARGO, TOTAL_TICKS = 13, 4, 7, 5, 140
MOVE_VECTORS = ((0, 0), (0, 1), (1, 0), (0, -1), (-1, 0))
OPPOSITE = (0, 3, 4, 1, 2)
BLUE_BASE, RED_BASE = (0, 0), (N - 1, N - 1)
# Map has exact 180-degree rotational symmetry.
WELL_SPECS = [
    (2, 3, 1, 1), (3, 2, 1, 1),
    (10, 9, 1, 1), (9, 10, 1, 1),
    (4, 8, 3, 3), (8, 4, 3, 3),
    (6, 6, 5, 5),
]


@dataclass
class Drone:
    x: int
    y: int
    units: int = 0
    cargo_value: int = 0

    def snapshot(self):
        return dict(x=self.x, y=self.y, units=self.units, cargo_value=self.cargo_value)


@dataclass
class Well:
    x: int
    y: int
    value: int
    period: int
    stock: int
    phase: int

    def snapshot(self):
        return dict(x=self.x, y=self.y, value=self.value, period=self.period,
                    stock=self.stock, phase=self.phase)


def rotate(x, y):
    return N - 1 - x, N - 1 - y


class Game:
    def __init__(self, seed: int):
        self.seed = seed
        rng = random.Random(seed)
        self.tick = 0
        self.scores = [0, 0]
        self.drones = [
            [Drone(*BLUE_BASE) for _ in range(DRONES)],
            [Drone(*RED_BASE) for _ in range(DRONES)],
        ]
        # Symmetric pairs receive identical initial stock and recharge phase.
        pair_settings = [(rng.randint(1, 3), rng.randrange(period))
                         for period in (1, 1, 3)]
        self.wells = []
        for i, (x, y, value, period) in enumerate(WELL_SPECS):
            if i < 6:
                pair_index = (0, 1, 0, 1, 2, 2)[i]
                stock, phase = pair_settings[pair_index]
            else:
                stock, phase = rng.randint(1, 3), rng.randrange(period)
            self.wells.append(Well(x, y, value, period, stock, phase))
        self.wells.sort(key=lambda w: (w.x, w.y))

    def observation(self, team: int) -> str:
        """One line of whitespace-delimited values; consistent for both players."""
        transform = (lambda x, y: (x, y)) if team == 0 else rotate
        parts = ["TURN", self.tick, self.scores[team], self.scores[1 - team]]
        for side in (team, 1 - team):
            for d in self.drones[side]:
                x, y = transform(d.x, d.y)
                parts += [x, y, d.units, d.cargo_value]
        visible_wells = []
        for w in self.wells:
            x, y = transform(w.x, w.y)
            visible_wells.append((x, y, w.value, w.period, w.stock, w.phase))
        for w in sorted(visible_wells):
            parts.extend(w)
        return " ".join(map(str, parts)) + "\n"

    def snapshot(self):
        return dict(tick=self.tick, scores=list(self.scores),
                    drones=[[d.snapshot() for d in side] for side in self.drones],
                    wells=[w.snapshot() for w in self.wells])

    def step(self, actions):
        if self.tick >= TOTAL_TICKS:
            raise RuntimeError("Game already ended")
        if len(actions) != 2 or any(len(a) != DRONES for a in actions):
            raise ValueError("Each player must provide exactly four actions")
        crashed = [[False] * DRONES for _ in range(2)]
        for team in range(2):
            for i, d in enumerate(self.drones[team]):
                a = actions[team][i]
                if type(a) is not int or not (0 <= a <= 4):
                    a = 0
                if team == 1:
                    a = OPPOSITE[a]
                dx, dy = MOVE_VECTORS[a]
                d.x = max(0, min(N - 1, d.x + dx))
                d.y = max(0, min(N - 1, d.y + dy))
        blue_pos = {(d.x, d.y) for d in self.drones[0]}
        red_pos = {(d.x, d.y) for d in self.drones[1]}
        contested = blue_pos & red_pos
        for team, base in enumerate((BLUE_BASE, RED_BASE)):
            for i, d in enumerate(self.drones[team]):
                if (d.x, d.y) in contested:
                    crashed[team][i] = True
                    d.x, d.y = base
                    d.units = d.cargo_value = 0
        # Deposit happens before harvesting; crashed drones skip both phases.
        for team, base in enumerate((BLUE_BASE, RED_BASE)):
            for i, d in enumerate(self.drones[team]):
                if not crashed[team][i] and (d.x, d.y) == base and d.units:
                    self.scores[team] += d.cargo_value
                    d.units = d.cargo_value = 0
        # On each well, at most one drone (lowest team, then ID) takes one packet.
        # The collision phase ensures both teams cannot harvest at the same square.
        for w in self.wells:
            if w.stock == 0:
                continue
            options = []
            for team in range(2):
                for i, d in enumerate(self.drones[team]):
                    if not crashed[team][i] and (d.x, d.y) == (w.x, w.y) and d.units < MAX_CARGO:
                        options.append((team, i))
            if options:
                team, i = min(options)
                d = self.drones[team][i]
                w.stock -= 1
                d.units += 1
                d.cargo_value += w.value
        self.tick += 1
        for w in self.wells:
            if (self.tick + w.phase) % w.period == 0:
                w.stock = min(MAX_CARGO, w.stock + 1)
        return crashed




# Season plugin contract used by the generic match runner.
class Season:
    max_turns = TOTAL_TICKS

    def __init__(self, seed):
        self.game = Game(seed)

    @property
    def turn(self):
        return self.game.tick

    def observe(self, team):
        return self.game.observation(team)

    def parse_action(self, team, line):
        try:
            actions = [int(value) for value in line.split()]
        except ValueError as exc:
            raise ValueError("action must contain integers") from exc
        if len(actions) != DRONES or any(x < 0 or x > 4 for x in actions):
            raise ValueError("expected exactly four integers in 0..4")
        return actions

    def step(self, actions):
        self.game.step(actions)

    def snapshot(self):
        return self.game.snapshot()

    def outcome(self):
        scores = list(self.game.scores)
        winner = (0 if scores[0] > scores[1] else
                  1 if scores[1] > scores[0] else None)
        return {"scores": scores, "winner": winner}


def create_game(seed):
    return Season(seed)
