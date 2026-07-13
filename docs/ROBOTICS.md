# Robotics and Embodiment

Seven's serial embodiment protocol is line-based UTF-8 at 9600 baud by default. The supported tools are `robot_status`, `robot_list_ports`, `robot_connect`, `robot_disconnect` and `robot_action`.

## Truthful outcomes

- `not_sent`: no device connection; nothing was queued or executed.
- `send_failed`: serial write failed.
- `sent_unacknowledged`: bytes were written but no `ACK` was received; execution is not claimed.
- `acknowledged`: the device returned a line beginning with `ACK`.
- `rejected`: invalid/unknown action or parameter.

This corrects the baseline behavior, which returned success for disconnected actions and called a volatile log entry a queue.

## Protocol

Host commands include `LED_ON`, `LED_OFF`, `LED_BLINK n`, `SERVO angle`, `SCAN`, `CELEBRATE`, `ALERT`, `IDLE_BREATHE`, `MOTOR_FWD speed`, `MOTOR_STOP` and `BUZZER`. Parameters are bounded before transmission.

Firmware replies with `ACK <command>` only after handling the command, or `ERR <reason>`. The reference sketch is `hardware/seven_robot/seven_robot.ino`. Its motor commands intentionally return `ERR MOTOR_DRIVER_NOT_CONFIGURED` until pins/driver are customized; it does not pretend generic motor hardware exists.

## Evidence boundary

Automated tests use a serial emulator to prove disconnected, acknowledged, unacknowledged, bounded and rejected behavior. Physical Arduino/Raspberry Pi and motor-driver tests remain required and will be recorded by board, firmware hash, port and result.
