// Official protocol adapter: do not modify for a competition entry.
#include "arena.hpp"
#include <iostream>
#include <array>
#include <string>
#include <exception>

namespace courier {
namespace {
std::array<int, DRONES> current_moves{};
}
void move(int drone_id, MoveMode direction) {
    if (drone_id < 0 || drone_id >= DRONES) return;
    int d = static_cast<int>(direction);
    current_moves[drone_id] = (d >= STAY && d <= LEFT) ? d : STAY;
}
}

int main() {
    using namespace courier;
    std::ios::sync_with_stdio(false);
    std::cin.tie(nullptr);
    std::string command;
    while (std::cin >> command) {
        if (command == "END") return 0;
        if (command != "TURN") return 2;
        State state;
        if (!(std::cin >> state.tick >> state.my_score >> state.enemy_score)) return 2;
        for (auto& d : state.me)
            if (!(std::cin >> d.x >> d.y >> d.units >> d.cargo_value)) return 2;
        for (auto& d : state.enemy)
            if (!(std::cin >> d.x >> d.y >> d.units >> d.cargo_value)) return 2;
        for (auto& w : state.wells)
            if (!(std::cin >> w.x >> w.y >> w.value >> w.period >> w.stock >> w.phase)) return 2;
        current_moves.fill(STAY);
        try {
            tick(state);
        } catch (const std::exception& ex) {
            std::cerr << "tick() threw: " << ex.what() << '\n';
            return 3;
        } catch (...) {
            std::cerr << "tick() threw an unknown exception\n";
            return 3;
        }
        for (int i = 0; i < DRONES; ++i) {
            if (i) std::cout << ' ';
            std::cout << current_moves[i];
        }
        std::cout << std::endl;  // flush, required for persistent bots
    }
    return 0;
}
