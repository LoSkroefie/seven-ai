import json

from seven.embodiment.bus import EmbodimentBus
from seven.tools import robotics_bus


class FakeSerial:
    def __init__(self, response=b"ACK LED_ON\n"):
        self.response = response
        self.written = []
        self.flushed = False
        self.closed = False

    def write(self, data): self.written.append(data)
    def flush(self): self.flushed = True
    def readline(self): return self.response
    def close(self): self.closed = True


def test_disconnected_action_is_not_reported_successful():
    bus = EmbodimentBus()
    assert bus.execute_named("led_on") is False
    assert bus.last_result["state"] == "not_sent"
    assert "not connected" in bus.last_result["error"]


def test_acknowledged_action_and_parameter_bounds():
    bus = EmbodimentBus()
    fake = FakeSerial(b"ACK SERVO 180\n")
    bus.conn, bus.connected = fake, True
    assert bus.execute_named("servo_move", {"angle": 999}) is True
    assert fake.written == [b"SERVO 180\n"]
    assert fake.flushed is True
    assert bus.last_result["state"] == "acknowledged"


def test_unacknowledged_and_unknown_actions_are_visible():
    bus = EmbodimentBus()
    bus.conn, bus.connected = FakeSerial(b""), True
    assert bus.execute_named("motor_forward", {"speed": -5}) is False
    assert bus.last_result["line"] == "MOTOR_FWD 0"
    assert bus.last_result["state"] == "sent_unacknowledged"
    assert bus.execute_named("invented_dance") is False
    assert bus.last_result["state"] == "rejected"


def test_missing_backend_never_claims_queue_or_delivery(monkeypatch):
    monkeypatch.setattr(robotics_bus, "_get_controller", lambda: None)
    result = robotics_bus.robot_action("led_on")
    assert result.startswith("ERROR:")
    assert "not sent" in result
    assert "queued" not in result
