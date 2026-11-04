// fake_bus.hpp — in-memory stand-in for an SO-101 servo bus (NOT compiled here).
#pragma once
#include <array>
#include <cstddef>

namespace so101_hw {

constexpr std::size_t kJoints = 6;

struct FakeBus {
  std::array<double, kJoints> position{};
  std::array<double, kJoints> velocity{};
  std::array<double, kJoints> command{};

  void read() {
    // Pretend the bus returns the last commanded position with zero velocity.
    for (std::size_t i = 0; i < kJoints; ++i) {
      position[i] = command[i];
      velocity[i] = 0.0;
    }
  }

  void write() {
    // Commands already sit in `command`; a real driver would encode STS frames.
  }
};

}  // namespace so101_hw
