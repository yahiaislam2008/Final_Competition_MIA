#!/usr/bin/env python3
import time
from enum import Enum, auto

import cv2
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from std_msgs.msg import Int32, Float32
from cv_bridge import CvBridge

from ultralytics import YOLO

#yousef 7at dol men cameraclass.py
from rclpy.qos import QoSProfile,ReliabilityPolicy,HistoryPolicy,DurabilityPolicy

qos_profile = QoSProfile(
    reliability=ReliabilityPolicy.BEST_EFFORT,
    durability=DurabilityPolicy.VOLATILE,
    history=HistoryPolicy.KEEP_LAST,
    depth=3
)

REAL_CLASS_NAME = 'real'

class State(Enum):
    SEARCH_BOX = auto()
    APPROACH_BOX = auto()
    CONFIRM_BOX = auto()
    REPOSITION = auto()
    DONE = auto()

class CameraState:
    SEARCH = 0
    APPROACH = 1
    STOP = 2
    COMPLETE = 3
    TURN = 4  # rotate-in-place phase of REPOSITION (controller must handle this value too)

class ScrollDetectionNode(Node):

    def __init__(self):
        super().__init__('scroll_detection_node')

        self.get_logger().info('Scroll detection node started')

        # ---------------- tunable parameters ----------------
        self.declare_parameter('confidence_threshold', 0.60)
        self.declare_parameter('confirm_frames', 5)
        self.declare_parameter('confirm_ratio', 0.7)        # fraction of buffer that must say "real"
        self.declare_parameter('approach_area_ratio', 0.12) # bbox area / frame area -> start slowing down
        self.declare_parameter('safe_stop_cm', 15.0)        # ultrasonic distance -> stop forward motion
        self.declare_parameter('reposition_forward_time', 1.5)
        self.declare_parameter('reposition_turn_time', 1.2)
        gp = self.get_parameter
        self.conf_thresh = gp('confidence_threshold').value
        self.confirm_frames = gp('confirm_frames').value
        self.confirm_ratio = gp('confirm_ratio').value
        self.approach_ratio = gp('approach_area_ratio').value
        self.safe_stop_cm = gp('safe_stop_cm').value
        self.reposition_fwd_t = gp('reposition_forward_time').value
        self.reposition_turn_t = gp('reposition_turn_time').value

        # ---------------- model ----------------
        self.model = YOLO("/media/yahia/DataDrive/MIA_TRANING/final_competition/Final_Competition_MIA/robot_competition/src/robot_competition/src/best.pt")

        # ---------------- I/O ----------------
        self.bridge = CvBridge()
        self.image_sub = self.create_subscription(Image,'/mono/image',self.image_callback,qos_profile)
        # Assuming this robot's firmware publishes /ultrasonic_distance as Float32 - verify with
        # `ros2 topic type /ultrasonic_distance` once, switch to Int32 here if that's wrong.
        self.ultra_float_sub = self.create_subscription(Float32,'/ultrasonic_distance',self.ultrasonic_float_callback,10)
        #7teb7et zy states 2l robot 2l moafrod yekon feha -> controller
        self.state_pub = self.create_publisher(Int32,'/camera_state',10)
        #bethowt boxes 3la 2l7aga
        self.debug_image_pub = self.create_publisher(Image,'/scroll_detection/debug_image',5)

        # ---------------- state ----------------
        self.state = State.SEARCH_BOX
        self.last_distance_cm = None
        self.boxes_confirmed = 0        # 0, 1, or 2
        self.confirm_buffer = []        # rolling list of bool (True = 'real' this frame)
        self.reposition_started_at = None
        self.last_published_state = None

        self.publish_camera_state(CameraState.SEARCH)

    # ------------------------------------------------------------------ #
    def ultrasonic_float_callback(self, msg):
        self.last_distance_cm = float(msg.data)

    def ultrasonic_int_callback(self, msg):
        self.last_distance_cm = float(msg.data)

    # ------------------------------------------------------------------ #
    def image_callback(self, msg):
        if self.state == State.DONE:
            return
        
        frame = self.bridge.imgmsg_to_cv2(msg,desired_encoding='bgr8')
        h, w = frame.shape[:2]
        detection, all_detections = self.best_detection(frame,w,h)

        self.publish_debug_image(frame, all_detections, msg.header)

        if self.state == State.SEARCH_BOX:
            self.do_search(detection)
        elif self.state == State.APPROACH_BOX:
            self.do_approach(detection, w)
        elif self.state == State.CONFIRM_BOX:
            self.do_confirm(detection)
        elif self.state == State.REPOSITION:
            self.do_reposition()

    # ------------------------------------------------------------------ #
    def best_detection(self, frame, frame_w, frame_h):

        results = self.model(frame,verbose=False)[0]
        best = None
        all_dets = []
        for box in results.boxes:
            conf = float(box.conf[0])
            if conf < self.conf_thresh:
                continue
            cls_name = self.model.names[int(box.cls[0])]
            x1, y1, x2, y2 = [float(v) for v in box.xyxy[0]]
            det = {
                'class': cls_name,
                'conf': conf,
                'cx': (x1 + x2) / 2.0,
                'area_ratio':((x2 - x1) * (y2 - y1)) / (frame_w * frame_h),
                'bbox': (x1, y1, x2, y2)
            }
            all_dets.append(det)
            if best is None or conf > best['conf']:
                best = det
        return best, all_dets

    # ------------------------------------------------------------------ #
    def publish_debug_image(self, frame, detections, header):
        """Draw every qualifying box (green=real, red=fake) plus current state/vote info
        and publish it, but only do the work if something is actually subscribed."""
        if self.debug_image_pub.get_subscription_count() == 0:
            return

        annotated = frame.copy()
        for det in detections:
            x1, y1, x2, y2 = [int(v) for v in det['bbox']]
            is_real = (det['class'] == REAL_CLASS_NAME)
            color = (0, 200, 0) if is_real else (0, 0, 220)  # BGR: green=real, red=fake
            cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 2)
            label = f"{det['class']} {det['conf']:.2f}"
            cv2.putText(annotated, label, (x1, max(0, y1 - 6)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

        status_lines = [f"state: {self.state.name}", f"confirmed: {self.boxes_confirmed}/2"]
        if self.state == State.CONFIRM_BOX and self.confirm_buffer:
            ratio = sum(self.confirm_buffer) / len(self.confirm_buffer)
            status_lines.append(f"vote: {ratio:.0%} ({len(self.confirm_buffer)}/{self.confirm_frames})")
        if self.last_distance_cm is not None:
            status_lines.append(f"ultrasonic: {self.last_distance_cm:.0f} cm")

        for i, line in enumerate(status_lines):
            cv2.putText(annotated, line, (8, 22 + 22 * i),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

        try:
            img_msg = self.bridge.cv2_to_imgmsg(annotated, encoding='bgr8')
            img_msg.header = header
            self.debug_image_pub.publish(img_msg)
        except Exception as e:
            self.get_logger().warn(f'Failed to publish debug image: {e}')

    # ------------------------------------------------------------------ #
    def do_search(self, det):
        """Rotate slowly in place until something is detected, then approach it."""
        if det is not None:
            self.get_logger().info(f"Candidate spotted ({det['class']}, {det['conf']:.2f})")
            self.state = State.APPROACH_BOX
            self.publish_camera_state(CameraState.APPROACH)

    def do_approach(self, det, frame_w):
        """Drive toward the candidate, centering it in frame, until close enough to slow down."""
        if det is None:
            self.get_logger().warn('Lost candidate - resuming search')
            self.state = State.SEARCH_BOX
            self.publish_camera_state(CameraState.SEARCH)
            return

        close_by_size = (det['area_ratio'] >self.approach_ratio)
        close_by_range = ((self.last_distance_cm is not None) and (self.last_distance_cm < (self.safe_stop_cm * 2)))

        if close_by_size or close_by_range:
            self.get_logger().info('Close to scroll - starting confirmation')
            self.confirm_buffer = []
            self.state = State.CONFIRM_BOX
            self.publish_camera_state(CameraState.STOP)
            return
        
        self.publish_camera_state(CameraState.APPROACH)

    def do_confirm(self, det):
        """Creep toward the box at low speed while voting on several frames before locking it in."""
        is_real = ((det is not None) and (det['class'] == REAL_CLASS_NAME))
        self.confirm_buffer.append(is_real)
        if len(self.confirm_buffer) > self.confirm_frames:
            self.confirm_buffer.pop(0)
        if len(self.confirm_buffer) < self.confirm_frames:
            return

        real_ratio = (sum(self.confirm_buffer)/ len(self.confirm_buffer))
        if real_ratio >= self.confirm_ratio:
            self.boxes_confirmed += 1
            self.get_logger().info(f"Scroll #{self.boxes_confirmed} confirmed")
            self.confirm_buffer = []
            if self.boxes_confirmed >= 2:
                self.finish()
            else:
                self.reposition_started_at = time.time()
                self.state = State.REPOSITION
                self.publish_camera_state(CameraState.APPROACH)
        else:
            self.get_logger().warn(f"Vote failed ({real_ratio:.0%})")
            self.confirm_buffer = []
            self.state = State.SEARCH_BOX
            self.publish_camera_state(CameraState.SEARCH)

    def do_reposition(self):
        """
        Fixed maneuver to move off the first box and line up on the second.
        Tune (or replace with waypoints) to match your side's actual field layout
        — Shato/Ulker start positions differ, and the map is reconfigured each round.
        """
        elapsed = (time.time() - self.reposition_started_at)
        if elapsed < self.reposition_turn_t:
            self.publish_camera_state(CameraState.TURN)
        elif elapsed < (self.reposition_turn_t + self.reposition_fwd_t):
            self.publish_camera_state(CameraState.APPROACH)
        else:
            self.get_logger().info('Reposition complete - searching for second scroll')
            self.state = State.SEARCH_BOX
            self.publish_camera_state(CameraState.SEARCH)

    def finish(self):
        self.state = State.DONE
        self.publish_camera_state(CameraState.COMPLETE)
        self.get_logger().info('Both scrolls confirmed - detection complete')

    def publish_camera_state(self, state):
        #is same cancel 
        if state == self.last_published_state:
            return

        msg = Int32()
        msg.data = state
        self.state_pub.publish(msg)
        self.last_published_state = state


def main(args=None):

    rclpy.init(args=args)
    node = ScrollDetectionNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()