#!/usr/bin/env python3

import time
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from std_msgs.msg import Int32
from pynput import keyboard


class Controller(Node):

    def __init__(self):
        super().__init__('controller')
        self.get_logger().info('Controller Node has been started.')

        self.declare_parameter('velocity','/cmd_vel')
        self.declare_parameter('camera_state_topic','/camera_state')

        self.declare_parameter('control_loop_period',0.05)
        self.declare_parameter('max_linear_speed',8.0)
        self.declare_parameter('max_angular_speed',4.0)
        self.declare_parameter('move_time',2.25)
        self.declare_parameter('rotate_90_time',1.28)
        # self.declare_parameter('rotate_180_time',3.0)
        # self.declare_parameter('rotate_360_time',6.0)

        self.cmd_vel = self.get_parameter('velocity').value
        self.camera_topic = self.get_parameter('camera_state_topic').value
        self.control_period = self.get_parameter('control_loop_period').value
        self.max_linear_speed = self.get_parameter('max_linear_speed').value
        self.max_angular_speed = self.get_parameter('max_angular_speed').value
        self.move_time = self.get_parameter('move_time').value
        self.rotate_90_time = self.get_parameter('rotate_90_time').value
        self.rotate_180_time = self.rotate_90_time * 2.0
        self.rotate_360_time = self.rotate_90_time * 4.0

        self.vel_publisher = self.create_publisher(Twist,self.cmd_vel,10)
        self.camera_subscriber = self.create_subscription(Int32,self.camera_topic,self.camera_state_callback,10)

        self.linear_vel_X = 0.0
        self.linear_vel_Y = 0.0
        self.angular_vel = 0.0
        self.camera_state = 0

        # False = Manual
        # True = Autonomous
        self.state = False
        self.auto_state = 'IDLE'
        self.state_start_time = time.time()

        self.listener = keyboard.Listener(
            on_press=self.on_press,
            on_release=self.on_release
        )

        self.listener.start()

        self.timer = self.create_timer(self.control_period,self.publish_velocity)

    def on_press(self, key):
        try:
            if key == keyboard.Key.up:
                self.moveForward()
            elif key == keyboard.Key.down:
                self.moveBackward()
            elif key == keyboard.Key.left:
                self.moveLeft()
            elif key == keyboard.Key.right:
                self.moveRight()
            elif hasattr(key, 'char') and key.char == 'a':
                self.turnLeft()
            elif hasattr(key, 'char') and key.char == 'd':
                self.turnRight()
            elif key == keyboard.Key.space:
                self.state = not self.state
                if self.state:
                    self.start_autonomous()
                else:
                    self.stop_autonomous()

        except AttributeError:
            pass

    def on_release(self, key):
        try:
            if (key == keyboard.Key.up or key == keyboard.Key.down):
                self.linear_vel_X = 0.0
            elif (key == keyboard.Key.left or key == keyboard.Key.right):
                self.linear_vel_Y = 0.0
            elif (hasattr(key, 'char') and key.char in ['a', 'd']):
                self.angular_vel = 0.0

        except AttributeError:
            pass

    def camera_state_callback(self, msg):
        self.camera_state = msg.data

    def moveForward(self):
        self.linear_vel_X = self.max_linear_speed

    def moveBackward(self):
        self.linear_vel_X = -self.max_linear_speed

    def moveLeft(self):
        self.linear_vel_Y = self.max_linear_speed

    def moveRight(self):
        self.linear_vel_Y = -self.max_linear_speed

    def turnLeft(self):
        self.angular_vel = self.max_angular_speed

    def turnRight(self):
        self.angular_vel = -self.max_angular_speed

    def start_autonomous(self):
        self.auto_state = 'START'
        self.state_start_time = time.time()
        self.linear_vel_X = 0.0
        self.linear_vel_Y = 0.0
        self.angular_vel = 0.0
        self.get_logger().info('AUTONOMOUS MODE')

    def stop_autonomous(self):
        self.auto_state = 'IDLE'
        self.linear_vel_X = 0.0
        self.linear_vel_Y = 0.0
        self.angular_vel = 0.0
        self.get_logger().info('MANUAL MODE')

    def autonomous(self):
        msg = Twist()
        elapsed = (time.time() - self.state_start_time)
        if self.auto_state == 'START':
            self.auto_state = 'MOVE_DIAGONAL'
            self.state_start_time = time.time()
            self.get_logger().info('AUTO: starting diagonal movement')

        elif self.auto_state == 'MOVE_DIAGONAL':
            msg.linear.x = self.max_linear_speed
            msg.linear.y = self.max_linear_speed - 1.0
            if elapsed >= self.move_time:
                self.auto_state = 'ROTATE_360'
                self.state_start_time = time.time()
                self.get_logger().info('AUTO: rotating 360 degrees')

        elif self.auto_state == 'ROTATE_360':
            msg.angular.z = self.max_angular_speed
            if elapsed >= self.rotate_360_time:
                self.auto_state = 'ROTATE_90'
                self.state_start_time = time.time()
                self.get_logger().info('AUTO: rotating 90 degrees')

        # elif self.auto_state == 'ROTATE_180':
        #     msg.angular.z = self.max_angular_speed
        #     if elapsed >= self.rotate_180_time:
        #         self.auto_state = 'ROTATE_90'
        #         self.state_start_time = time.time()
        #         self.get_logger().info('AUTO: rotating 90 degrees')

        elif self.auto_state == 'ROTATE_90':
            msg.angular.z = self.max_angular_speed
            if elapsed >= self.rotate_90_time:
                self.auto_state = 'SEARCH'
                self.state_start_time = time.time()
                self.get_logger().info('AUTO: searching for scrolls')

        elif self.auto_state == 'SEARCH':
            if self.camera_state == 0:
                msg.linear.x = 0.0 
                msg.angular.z = self.max_angular_speed

            elif self.camera_state == 1:

                msg.linear.x = self.max_linear_speed

            elif self.camera_state == 2:

                msg.linear.x = 0.0
                msg.linear.y = 0.0
                msg.angular.z = 0.0

            elif self.camera_state == 3:

                msg.linear.x = 0.0
                msg.linear.y = 0.0
                msg.angular.z = 0.0

            elif self.camera_state == 4:
                # TURN: rotate-in-place phase of the scroll node's REPOSITION maneuver
                msg.linear.x = 0.0
                msg.linear.y = 0.0
                msg.angular.z = self.max_angular_speed
        return msg

    def publish_velocity(self):

        if not self.state:

            msg = Twist()

            msg.linear.x = self.linear_vel_X
            msg.linear.y = self.linear_vel_Y
            msg.angular.z = self.angular_vel

        else:

            msg = self.autonomous()

        self.vel_publisher.publish(msg)


def main(args=None):
    rclpy.init(args=args)
    node = Controller()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.listener.stop()
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
