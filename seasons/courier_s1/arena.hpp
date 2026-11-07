#ifndef COURIER_CLASH_ARENA_HPP
#define COURIER_CLASH_ARENA_HPP

#include <array>

namespace courier {
constexpr int N = 13;
constexpr int DRONES = 4;
constexpr int WELLS = 7;
constexpr int MAX_CARGO = 5;
constexpr int TOTAL_TICKS = 140;

enum MoveMode : int { STAY = 0, UP = 1, RIGHT = 2, DOWN = 3, LEFT = 4 };

struct Drone {
    int x = 0, y = 0;
    int units = 0;       // Number of collected packets, max MAX_CARGO.
    int cargo_value = 0; // Total unbanked score; 0 after delivery/crash.
};

struct Well {
    int x = 0, y = 0;
    int value = 0;       // Points per collected packet.
    int period = 0;      // Recharge period (ticks per +1 stock).
    int stock = 0;       // Available packets, max MAX_CARGO.
    int phase = 0;       // Regenerates after ticks t with (t + phase) % period == 0.
};

struct State {
    int tick = 0;       // 0..TOTAL_TICKS-1
    int my_score = 0;
    int enemy_score = 0;
    std::array<Drone, DRONES> me{};
    std::array<Drone, DRONES> enemy{};
    std::array<Well, WELLS> wells{};
};

// You implement this function; called once per tick.
void tick(const State& state);

// Call once per drone every tick. Unspecified drones STAY.
// All coordinates you see are in your team's local perspective:
// your base (0,0), enemy base (12,12), x rightwards, y upwards.
void move(int drone_id, MoveMode direction);
}  // namespace courier

#endif
