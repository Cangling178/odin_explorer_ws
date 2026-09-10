# Lower-level firmware

The owner has an F4 lower-level controller. Exact chip, board, existing firmware
and toolchain remain unverified. The proposed responsibility is two wheel-speed
loops, encoder capture, PWM/direction output, feedback and a command watchdog. Keep firmware
source, build instructions, pin map and protocol versions here once known.
Do not invent F4 timer channels, encoder pins, PWM polarity or flash settings
before inspecting the actual board and motor driver.
