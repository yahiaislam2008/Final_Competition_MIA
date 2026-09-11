#!/usr/bin/env python3
import rclpy
import time
from rclpy.node import Node
from geometry_msgs.msg import Twist
from std_msgs.msg import Float32
from pynput import keyboard


class Controller(Node):

    def __init__(self):
        super().__init__('controller')

        self.get_logger().info('Controller Node has been started.')

        self.declare_parameter('velocity', '/cmd_vel')
        self.declare_parameter('ultrasonic_topic', '/ultrasonic_distance')

        self.declare_parameter('control_loop_period', 0.05)

        self.declare_parameter('max_linear_speed', 4.0)
        self.declare_parameter('max_angular_speed', 2.0)

        self.declare_parameter('wall_distance', 0.30)
        self.declare_parameter('wall_tolerance', 0.05)

        self.declare_parameter('rotate_90_time', 1.5)
        self.declare_parameter('rotate_180_time', 3.0)

        # Manual / Autonomous mode
        # False = Manual
        # True  = Autonomous
        self.declare_parameter('state', False)

        ultrasonic_topic = self.get_parameter('ultrasonic_topic').get_parameter_value().string_value

        self.cmd_vel = self.get_parameter('velocity').get_parameter_value().string_value

        self.control_period = self.get_parameter('control_loop_period').value

        self.max_linear_speed = self.get_parameter('max_linear_speed').value

        self.max_angular_speed = self.get_parameter('max_angular_speed').value

        self.state = self.get_parameter('state').value

        self.wall_distance = self.get_parameter('wall_distance').value

        self.wall_tolerance = self.get_parameter('wall_tolerance').value

        self.rotate_90_time = self.get_parameter('rotate_90_time').value

        self.rotate_180_time = self.get_parameter('rotate_180_time').value

        self.vel_publisher = self.create_publisher(Twist,self.cmd_vel,10)
        self.ultrasonic_subscriber = self.create_subscription(Float32,ultrasonic_topic,self.ultrasonic_callback,10)
        
        self.linear_vel_X = 0.0
        self.linear_vel_Y = 0.0
        self.angular_vel = 0.0

        self.ultrasonic_distance = None

        self.listener = keyboard.Listener(on_press=self.on_press, on_release=self.on_release)

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
                    self.get_logger().info('AUTONOMOUS MODE')

                    self.auto_state = 'START'
                    self.state_start_time = time.time()
                else:
                    self.get_logger().info('MANUAL MODE')

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

    def ultrasonic_callback(self, msg):
        self.ultrasonic_distance = msg.data

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

    def autonomous(self, msg):
        # This function is a placeholder for the autonomous controller logic.
        # You can implement your autonomous control logic here.
        pass
    
    def publish_velocity(self):
        msg = Twist()

        if not self.state:

            msg.linear.x = self.linear_vel_X
            msg.linear.y = self.linear_vel_Y
            msg.angular.z = self.angular_vel

        else:
            # leave it for the autonomous controller to handle the velocity commands later
            self.autonomous(msg)

        self.vel_publisher.publish(msg)

def main(args=None):

    rclpy.init(args=args)
    controller = Controller()

    try:
        rclpy.spin(controller)
    except KeyboardInterrupt:
        pass

    finally:
        # Stop robot before shutting down
        msg = Twist()
        controller.vel_publisher.publish(msg)
        controller.listener.stop()
        controller.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':

    main()