#include "arena.hpp"
using namespace courier;

// Interface demonstration ONLY, intentionally not a useful strategy.
// Competitors are given this file; everything else is up to them.
void courier::tick(const State& s) {
    for (int i = 0; i < DRONES; ++i) {
        move(i, STAY);
    }
}
