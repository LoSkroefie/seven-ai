"""
Hardware Embodiment / Robotics Hooks — Seven AI v3.2

Gives Seven a physical presence through Arduino/RPi GPIO control.
Actions are triggered by emotion states, goal completions, and
autonomous decisions.

Supported hardware:
- Arduino (via pySerial): LED, servo, motor, buzzer
- Raspberry Pi GPIO (via RPi.GPIO): direct pin control

All commands are sandboxed:
- User confirmation required for first connection
- Command whitelist prevents arbitrary serial injection
- Timeout on all operations
- Configurable port/baud in config.py

100% local. No network calls.
"""

import json
import logging
import time
import threading
from typing import Optional, Dict, List, Any, Callable
from datetime import datetime
from enum import Enum

logger = logging.getLogger("Robotics")

# Optional imports
SERIAL_AVAILABLE = False
GPIO_AVAILABLE = False

try:
    import serial
    import serial.tools.list_ports
    SERIAL_AVAILABLE = True
except ImportError:
    pass

try:
    import RPi.GPIO as GPIO
    GPIO_AVAILABLE = True
except ImportError:
    pass


class RobotAction(Enum):
    """Safe, whitelisted robot actions"""
    LED_ON = "led_on"
    LED_OFF = "led_off"
    LED_BLINK = "led_blink"
    SERVO_MOVE = "servo_move"
    MOTOR_FORWARD = "motor_forward"
    MOTOR_STOP = "motor_stop"
    BUZZER_BEEP = "buzzer_beep"
    BUZZER_TONE = "buzzer_tone"
    SCAN = "scan"           # Sweep servo (curious behavior)
    CELEBRATE = "celebrate"  # LED blink + buzzer (happy)
    ALERT = "alert"         # Fast blink + tone (danger/fear)
    IDLE_BREATHE = "idle_breathe"  # Slow LED pulse (resting)
    CUSTOM = "custom"       # User-defined via extensions


# Emotion → Action mapping (default)
EMOTION_ACTION_MAP = {
    'joy': [RobotAction.CELEBRATE],
    'happiness': [RobotAction.LED_BLINK, RobotAction.BUZZER_BEEP],
    'curiosity': [RobotAction.SCAN],
    'surprise': [RobotAction.LED_BLINK, RobotAction.BUZZER_TONE],
    'fear': [RobotAction.ALERT],
    'anger': [RobotAction.ALERT],
    'sadness': [RobotAction.LED_OFF],
    'calm': [RobotAction.IDLE_BREATHE],
    'excitement': [RobotAction.CELEBRATE, RobotAction.MOTOR_FORWARD],
    'love': [RobotAction.LED_BLINK],
}


class SerialDevice:
    """Safe serial connection to Arduino/microcontroller"""
    
    COMMAND_WHITELIST = {
        'LED_ON', 'LED_OFF', 'LED_BLINK',
        'SERVO', 'MOTOR_FWD', 'MOTOR_STOP', 'MOTOR_REV',
        'BUZZER', 'BUZZER_TONE', 'SCAN', 'NOOP'
    }
    
    def __init__(self, port: str, baud: int = 9600, timeout: float = 2.0):
        self.port = port
        self.baud = baud
        self.timeout = timeout
        self.connection: Optional[serial.Serial] = None
        self.lock = threading.Lock()
        self.connected = False
        self.last_command_time: Optional[datetime] = None
    
    def connect(self) -> bool:
        """Connect to serial device"""
        if not SERIAL_AVAILABLE:
            logger.warning("[ROBOTICS] pyserial not available")
            return False
        
        try:
            self.connection = serial.Serial(
                port=self.port,
                baudrate=self.baud,
                timeout=self.timeout
            )
            time.sleep(2)  # Arduino reset delay
            self.connected = True
            logger.info(f"[ROBOTICS] Connected to {self.port} @ {self.baud} baud")
            return True
        except Exception as e:
            logger.error(f"[ROBOTICS] Connection failed ({self.port}): {e}")
            self.connected = False
            return False
    
    def disconnect(self):
        """Disconnect from serial device"""
        if self.connection and self.connection.is_open:
            try:
                self.connection.close()
            except Exception:
                pass
        self.connected = False
        logger.info(f"[ROBOTICS] Disconnected from {self.port}")
    
    def send_command(self, command: str, value: str = "") -> bool:
        """
        Send a whitelisted command to the device.
        Format: COMMAND:VALUE\n (e.g., SERVO:90\n)
        """
        # Sanitize — only allow whitelisted commands
        cmd_upper = command.upper().strip()
        if cmd_upper not in self.COMMAND_WHITELIST:
            logger.warning(f"[ROBOTICS] Blocked non-whitelisted command: {command}")
            return False
        
        if not self.connected or not self.connection:
            logger.debug("[ROBOTICS] Not connected — skipping command")
            return False
        
        with self.lock:
            try:
                msg = f"{cmd_upper}:{value}\n" if value else f"{cmd_upper}\n"
                self.connection.write(msg.encode('ascii'))
                self.connection.flush()
                self.last_command_time = datetime.now()
                logger.debug(f"[ROBOTICS] Sent: {msg.strip()}")
                return True
            except Exception as e:
                logger.error(f"[ROBOTICS] Send error: {e}")
                self.connected = False
                return False
    
    def read_response(self, timeout: float = 1.0) -> Optional[str]:
        """Read response from device"""
        if not self.connected or not self.connection:
            return None
        
        with self.lock:
            try:
                self.connection.timeout = timeout
                line = self.connection.readline().decode('ascii', errors='ignore').strip()
                return line if line else None
            except Exception:
                return None
    
    @staticmethod
    def list_ports() -> List[Dict[str, str]]:
        """List available serial ports"""
        if not SERIAL_AVAILABLE:
            return []
        
        ports = []
        for port in serial.tools.list_ports.comports():
            ports.append({
                'port': port.device,
                'description': port.description,
                'hwid': port.hwid
            })
        return ports


class RoboticsController:
    """
    Main robotics controller for Seven AI.
    
    Translates emotions, goals, and autonomous decisions into
    physical actions via serial devices or GPIO pins.
    
    Thread-safe. Sandboxed. User-confirmable.
    """
    
    def __init__(self, bot=None, config: Dict = None):
        self.bot = bot
        self.config = config or {}
        
        # Devices
        self.serial_device: Optional[SerialDevice] = None
        self.gpio_pins: Dict[str, int] = {}  # name -> pin number
        
        # State
        self.enabled = False
        self.user_confirmed = False  # Must be confirmed before hardware access
        self.action_log: List[Dict] = []
        self.emotion_actions = dict(EMOTION_ACTION_MAP)
        self.custom_actions: Dict[str, Callable] = {}
        
        # Config
        self.serial_port = self.config.get('serial_port', '')
        self.serial_baud = self.config.get('serial_baud', 9600)
        self.auto_connect = self.config.get('auto_connect', False)
        
        # Load custom emotion mapping if exists
        self._load_emotion_map()
        
        logger.info(
            f"[ROBOTICS] Initialized — serial={'available' if SERIAL_AVAILABLE else 'no'}, "
            f"gpio={'available' if GPIO_AVAILABLE else 'no'}, "
            f"port={self.serial_port or 'not configured'}"
        )
    
    def confirm_hardware_access(self) -> bool:
        """
        User must explicitly confirm hardware access.
        Called from GUI or CLI before any commands are sent.
        """
        self.user_confirmed = True
        self.enabled = True
        logger.info("[ROBOTICS] Hardware access confirmed by user")
        return True
    
    def connect(self) -> bool:
        """Connect to hardware"""
        if not self.user_confirmed:
            logger.warning("[ROBOTICS] Cannot connect — user confirmation required")
            return False
        
        if self.serial_port and SERIAL_AVAILABLE:
            self.serial_device = SerialDevice(
                port=self.serial_port,
                baud=self.serial_baud
            )
            return self.serial_device.connect()
        
        if GPIO_AVAILABLE:
            self._setup_gpio()
            return True
        
        logger.warning("[ROBOTICS] No hardware available to connect")
        return False
    
    def disconnect(self):
        """Disconnect from all hardware"""
        if self.serial_device:
            self.serial_device.disconnect()
        
        if GPIO_AVAILABLE:
            try:
                GPIO.cleanup()
            except Exception:
                pass
        
        self.enabled = False
    
    def _setup_gpio(self):
        """Setup Raspberry Pi GPIO pins"""
        if not GPIO_AVAILABLE:
            return
        
        try:
            GPIO.setmode(GPIO.BCM)
            
            # Default pin mapping (configurable)
            self.gpio_pins = self.config.get('gpio_pins', {
                'led': 18,
                'servo': 12,
                'buzzer': 25,
                'motor_a': 23,
                'motor_b': 24
            })
            
            for name, pin in self.gpio_pins.items():
                GPIO.setup(pin, GPIO.OUT)
                GPIO.output(pin, GPIO.LOW)
            
            logger.info(f"[ROBOTICS] GPIO initialized: {self.gpio_pins}")
        except Exception as e:
            logger.error(f"[ROBOTICS] GPIO setup error: {e}")
    
    # ==================== Action Execution ====================
    
    def execute_action(self, action: RobotAction, params: Dict = None) -> bool:
        """Execute a robot action (sandboxed)"""
        if not self.enabled or not self.user_confirmed:
            return False
        
        params = params or {}
        success = False
        
        try:
            if action == RobotAction.LED_ON:
                success = self._cmd('LED_ON')
            elif action == RobotAction.LED_OFF:
                success = self._cmd('LED_OFF')
            elif action == RobotAction.LED_BLINK:
                success = self._cmd('LED_BLINK', str(params.get('count', 3)))
            elif action == RobotAction.SERVO_MOVE:
                angle = max(0, min(180, params.get('angle', 90)))
                success = self._cmd('SERVO', str(angle))
            elif action == RobotAction.MOTOR_FORWARD:
                success = self._cmd('MOTOR_FWD', str(params.get('speed', 128)))
            elif action == RobotAction.MOTOR_STOP:
                success = self._cmd('MOTOR_STOP')
            elif action == RobotAction.BUZZER_BEEP:
                success = self._cmd('BUZZER', str(params.get('duration', 200)))
            elif action == RobotAction.BUZZER_TONE:
                success = self._cmd('BUZZER_TONE', str(params.get('freq', 440)))
            elif action == RobotAction.SCAN:
                success = self._cmd('SCAN')
            elif action == RobotAction.CELEBRATE:
                self._cmd('LED_BLINK', '5')
                success = self._cmd('BUZZER', '100')
            elif action == RobotAction.ALERT:
                self._cmd('LED_BLINK', '10')
                success = self._cmd('BUZZER_TONE', '880')
            elif action == RobotAction.IDLE_BREATHE:
                success = self._cmd('LED_BLINK', '1')
            elif action == RobotAction.CUSTOM:
                handler = self.custom_actions.get(params.get('name', ''))
                if handler:
                    handler(params)
                    success = True
            
            # Log action
            self.action_log.append({
                'action': action.value,
                'params': params,
                'success': success,
                'timestamp': datetime.now().isoformat()
            })
            
            # Trim log
            if len(self.action_log) > 200:
                self.action_log = self.action_log[-100:]
            
        except Exception as e:
            logger.error(f"[ROBOTICS] Action error ({action.value}): {e}")
        
        return success
    
    def _cmd(self, command: str, value: str = "") -> bool:
        """Send command to active device"""
        if self.serial_device and self.serial_device.connected:
            return self.serial_device.send_command(command, value)
        
        if GPIO_AVAILABLE and self.gpio_pins:
            return self._gpio_command(command, value)
        
        logger.debug(f"[ROBOTICS] No device — simulating: {command}:{value}")
        return True  # Simulate success when no hardware
    
    def _gpio_command(self, command: str, value: str = "") -> bool:
        """Execute command via GPIO"""
        if not GPIO_AVAILABLE:
            return False
        
        try:
            if command == 'LED_ON' and 'led' in self.gpio_pins:
                GPIO.output(self.gpio_pins['led'], GPIO.HIGH)
            elif command == 'LED_OFF' and 'led' in self.gpio_pins:
                GPIO.output(self.gpio_pins['led'], GPIO.LOW)
            elif command == 'BUZZER' and 'buzzer' in self.gpio_pins:
                pin = self.gpio_pins['buzzer']
                GPIO.output(pin, GPIO.HIGH)
                ms = int(value) if value else 200
                time.sleep(ms / 1000)
                GPIO.output(pin, GPIO.LOW)
            else:
                return False
            return True
        except Exception as e:
            logger.error(f"[ROBOTICS] GPIO error: {e}")
            return False
    
    # ==================== Emotion Integration ====================
    
    def on_emotion_change(self, emotion: str, intensity: float = 0.5):
        """
        Called when Seven's emotion changes.
        Maps emotion to physical actions.
        
        Only triggers if intensity > 0.4 (avoid reacting to weak emotions)
        """
        if not self.enabled or intensity < 0.4:
            return
        
        emotion_lower = emotion.lower()
        actions = self.emotion_actions.get(emotion_lower, [])
        
        for action in actions:
            self.execute_action(action, {'intensity': intensity})
    
    def on_goal_completed(self, goal_name: str):
        """Called when a goal is completed — celebrate!"""
        if self.enabled:
            self.execute_action(RobotAction.CELEBRATE)
    
    def on_user_arrives(self):
        """Called when user interaction detected after idle"""
        if self.enabled:
            self.execute_action(RobotAction.LED_ON)
            self.execute_action(RobotAction.BUZZER_BEEP, {'duration': 100})
    
    def on_sleep(self):
        """Called when Seven enters sleep/dream mode"""
        if self.enabled:
            self.execute_action(RobotAction.IDLE_BREATHE)
    
    # ==================== Extension Support ====================
    
    def register_action(self, name: str, handler: Callable):
        """Register a custom action handler from an extension"""
        self.custom_actions[name] = handler
        logger.info(f"[ROBOTICS] Registered custom action: {name}")
    
    def _load_emotion_map(self):
        """Load custom emotion-action mapping from config"""
        custom_map = self.config.get('emotion_action_map', {})
        for emotion, actions in custom_map.items():
            try:
                self.emotion_actions[emotion] = [
                    RobotAction(a) for a in actions
                ]
            except (ValueError, KeyError):
                pass
    
    # ==================== Status ====================
    
    def get_status(self) -> Dict[str, Any]:
        """Get robotics status for GUI/API"""
        return {
            'available': SERIAL_AVAILABLE or GPIO_AVAILABLE,
            'enabled': self.enabled,
            'user_confirmed': self.user_confirmed,
            'serial_connected': (
                self.serial_device.connected if self.serial_device else False
            ),
            'serial_port': self.serial_port,
            'gpio_available': GPIO_AVAILABLE,
            'gpio_pins': self.gpio_pins if GPIO_AVAILABLE else {},
            'total_actions': len(self.action_log),
            'recent_actions': self.action_log[-5:],
            'custom_actions': list(self.custom_actions.keys()),
            'available_ports': SerialDevice.list_ports() if SERIAL_AVAILABLE else []
        }
    
    @staticmethod
    def list_available_ports() -> List[Dict[str, str]]:
        """List available serial ports for GUI/config"""
        return SerialDevice.list_ports()
