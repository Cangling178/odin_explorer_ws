# Motor transport contract, proposed

Choose the Jetson-to-F4 transport after inspecting the board; CAN or UART/USB
serial are candidates, not confirmed wiring.
Document physical transport, bitrate, packet framing, byte order and scaling.

Required semantics: protocol version; monotonic sequence; explicit enable;
bounded physical velocity targets; feedback wheel positions/velocities; fault
flags; command age; heartbeat; corruption detection; and restart behavior.
Reject malformed, stale, nonfinite and out-of-range commands. An old packet must
not re-enable motion after a stop. Timeout behavior belongs in the lower-level
controller and must be exercised with a disconnected host.

Tests before integration: valid round trip, truncated packet, bad checksum,
duplicate/out-of-order sequence, reconnect, target saturation and watchdog.
There is no transport implementation or flashed firmware in this foundation.

## Proposed host/F4 boundary

The host differential controller converts body velocity to left/right wheel
rad/s. The F4 accepts these physical wheel targets, applies enable/watchdog
logic and closes feedback loops if encoders are present. Feedback should include
accumulated wheel counts or position, wheel speed, status and device sample time.
Document wraparound and clock conversion. Do not run another independent body
kinematics layer on the F4 unless the host contract is deliberately revised.

Organize future code as board support, encoder input, motor output, velocity
control, communications and fault/enable state. Select HAL/LL, RTOS or bare-metal
and the build system only after examining existing firmware and peripheral needs.
