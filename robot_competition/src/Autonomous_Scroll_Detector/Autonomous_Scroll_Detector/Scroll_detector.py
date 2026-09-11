from enum import Enum, auto

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from std_msgs.msg import Float32, String


class State(Enum):
    SCAN = auto()
    ALIGN = auto()
    APPROACH = auto()
    RETREAT = auto()
    DONE = auto()


class NavigationNode(Node):
    def __init__(self):
        super().__init__('navigation_node')

        # ---- tunable parameters ----
        self.declare_parameter('cmd_vel_topic', '/cmd_vel')
        self.declare_parameter('ultrasonic_topic', '/ultrasonic_distance')
        self.declare_parameter('scan_speed', 0.10)             # Horizontal speed
        self.declare_parameter('approach_speed', 0.12)         # forward speed
        self.declare_parameter('detection_max_range', 1.0)     # Object detected
        self.declare_parameter('clear_margin', 0.15)           # m, added to detection_max_range to confirm "cleared" (hysteresis)
        self.declare_parameter('approach_stop_distance', 0.12) # Stop when scroll is below this distance
        self.declare_parameter('scan_timeout_s', 20.0)         # bail out of SCAN if stuck
        self.declare_parameter('align_timeout_s', 8.0)         # bail out of ALIGN if stuck
        self.declare_parameter('approach_timeout_s', 6.0)      # bail out of APPROACH if stuck
        self.declare_parameter('retreat_timeout_s', 6.0)       # bail out of RETREAT if stuck
        self.declare_parameter('control_rate_hz', 20.0)

        self.cmd_vel_topic = self.get_parameter('cmd_vel_topic').value
        self.ultrasonic_topic = self.get_parameter('ultrasonic_topic').value
        self.scan_speed = self.get_parameter('scan_speed').value
        self.approach_speed = self.get_parameter('approach_speed').value
        self.detection_max_range = self.get_parameter('detection_max_range').value
        self.clear_margin = self.get_parameter('clear_margin').value
        self.approach_stop_distance = self.get_parameter('approach_stop_distance').value
        self.scan_timeout_s = self.get_parameter('scan_timeout_s').value
        self.align_timeout_s = self.get_parameter('align_timeout_s').value
        self.approach_timeout_s = self.get_parameter('approach_timeout_s').value
        self.retreat_timeout_s = self.get_parameter('retreat_timeout_s').value
        control_rate = self.get_parameter('control_rate_hz').value
        self.dt = 1.0 / control_rate

        self.clear_threshold = self.detection_max_range + self.clear_margin

        # pub/sub
        self.pub_cmd = self.create_publisher(Twist, self.cmd_vel_topic, 10)
        self.pub_state = self.create_publisher(String, '/nav_state', 10)
        self.create_subscription(Float32, self.ultrasonic_topic, self.on_ultrasonic, 10)

        # state
        self.state = State.SCAN
        self.latest_distance = None
        self.scan_direction = 1.0        # +1 or -1, the direction used throughout SCAN
        self._below_threshold = False    # for edge detection

        self.scrolls = []             # [{'order': 0/1, 'distance': float}], in order found
        self.current_index = None        # which candidate's location the robot is physically at
        self.targets_queue = []          # ordered [near, far] once comparison is done
        self.current_target = None

        self._state_elapsed = 0.0        # safety timeouts timer

        self.timer = self.create_timer(self.dt, self.control_loop)
        self.get_logger().info("navigation_node started in state SCAN")

    # ultrasonic reading
    def on_ultrasonic(self, msg: Float32):
        self.latest_distance = float(msg.data)

    # cmd_vel
    def publish_cmd(self, vx: float, vy: float):
        t = Twist()
        t.linear.x = float(vx)
        t.linear.y = float(vy)
        self.pub_cmd.publish(t)

    def stop(self):
        self.publish_cmd(0.0, 0.0)

    def publish_state(self):
        self.pub_state.publish(String(data=self.state.name))

    def _set_state(self, new_state: State):
        self.state = new_state
        self._state_elapsed = 0.0



    def control_loop(self):
        self.publish_state()

        if self.latest_distance is None:
            self.stop()  
            return

        self._state_elapsed += self.dt

        if self.state == State.SCAN:
            self._do_scan()
        elif self.state == State.ALIGN:
            self._do_align()
        elif self.state == State.APPROACH:
            self._do_approach()
        elif self.state == State.RETREAT:
            self._do_retreat()
        elif self.state == State.DONE:
            self.stop()

    # SCAN
    def _do_scan(self):
        is_below = self.latest_distance < self.detection_max_range

        # a scroll just came into range directly ahead
        if is_below and not self._below_threshold:
            order = len(self.scrolls)
            self.scrolls.append({'order': order, 'distance': self.latest_distance})
            self.get_logger().info(
                f"Scroll candidate #{order} recorded at distance={self.latest_distance:.2f} m")
        self._below_threshold = is_below

        if len(self.scrolls) >= 2:
            self.stop()
            self.current_index = self.scrolls[-1]['order']  # we're physically at the last one found
            self._start_comparison()
            return

        # safety-only bail-out: never used for targeting, just prevents an
        # infinite strafe into a wall if a second scroll is never detected
        if self._state_elapsed > self.scan_timeout_s:
            self.stop()
            self.get_logger().error(
                "SCAN timed out without finding 2 scrolls. Stopping. "
                "Check detection_max_range / scan_speed / physical setup.")
            self._set_state(State.DONE)
            return

        self.publish_cmd(0.0, self.scan_direction * self.scan_speed)

    # ALIGN
    def _start_comparison(self):
        near, far = sorted(self.scrolls, key=lambda c: c['distance'])
        self.targets_queue = [near, far]
        self.get_logger().info(
            f"Comparison done. Near candidate distance={near['distance']:.2f} m "
            f"(order={near['order']}), far candidate distance={far['distance']:.2f} m "
            f"(order={far['order']}). Going for near first.")
        self._pop_next_target()

    def _pop_next_target(self):
        if not self.targets_queue:
            self._set_state(State.DONE)
            self.get_logger().info("Both scrolls handled. Search complete.")
            return

        self.current_target = self.targets_queue.pop(0)
        self._below_threshold = self.latest_distance < self.detection_max_range

        if self.current_target['order'] == self.current_index:
            # already at this candidate's location (e.g. it was the last one
            # found in SCAN) - no strafing needed, go straight to APPROACH
            self.get_logger().info("Target is the current position skipping ALIGN.")
            self._set_state(State.APPROACH)
        else:
            # moving toward a higher order index = same direction as the
            # original scan; moving toward a lower index = reverse it
            self._align_direction = (
                self.scan_direction if self.current_target['order'] > self.current_index
                else -self.scan_direction
            )
            self._set_state(State.ALIGN)
            self.get_logger().info(
                f"Aligning toward order={self.current_target['order']} "
                f"(direction={'+' if self._align_direction > 0 else '-'})")

    def _do_align(self):
        """Strafe toward the target until the ultrasonic re-detects it
        (falling edge). Purely sensor-triggered - no position estimate."""
        d = self.latest_distance
        is_below = d < self.detection_max_range
        reconfirmed = is_below and not self._below_threshold
        self._below_threshold = is_below

        if reconfirmed:
            self.stop()
            self.current_index = self.current_target['order']
            self.get_logger().info("Re-detected target while aligning. Approaching.")
            self._set_state(State.APPROACH)
            return

        # safety-only bail-out: prevents strafing forever (into a wall) if
        # re-detection never happens - not used for targeting logic
        if self._state_elapsed > self.align_timeout_s:
            self.stop()
            self.get_logger().error(
                "ALIGN timed out without re-detecting the target. Skipping it "
                "and moving on to avoid driving blind.")
            self._pop_next_target()
            return

        self.publish_cmd(0.0, self._align_direction * self.scan_speed)

    # APPROACH
    def _do_approach(self):
        """Drive straight at the target using live ultrasonic distance,
        stopping short of contact (avoids the -2 pt hit-the-scroll penalty)."""
        d = self.latest_distance
        if d <= self.approach_stop_distance:
            self.stop()
            self.get_logger().info(f"Reached target (distance={d:.2f} m). Retreating to scan line.")
            self._below_threshold = True  # we know we're currently "under threshold"
            self._set_state(State.RETREAT)
            return
        if self._state_elapsed > self.approach_timeout_s:
            self.stop()
            self.get_logger().error(
                "APPROACH timed out before reaching stop distance "
                f"(last reading={d:.2f} m). Retreating instead of continuing blind.")
            self._below_threshold = True
            self._set_state(State.RETREAT)
            return
 

        self.publish_cmd(self.approach_speed, 0.0)

    # RETREAT
    def _do_retreat(self):
        d = self.latest_distance

        if d >= self.clear_threshold:
            self.stop()
            self._below_threshold = False
            self.get_logger().info("Cleared target on retreat. Ready for next step.")
            self._pop_next_target()
            return

        # Saftey timeout
        if self._state_elapsed > self.retreat_timeout_s:
            self.get_logger().error("RETREAT timed out without clearing. Stopping to avoid driving blind.")
            self.stop()
            self._pop_next_target()
            return

        self.publish_cmd(-self.approach_speed, 0.0)


def main(args=None):
    rclpy.init(args=args)
    node = NavigationNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.stop()
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()