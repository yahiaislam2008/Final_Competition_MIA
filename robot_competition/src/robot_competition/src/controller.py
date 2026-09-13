# # # #!/usr/bin/env python3

# # # import rclpy
# # # import time

# # # from rclpy.node import Node
# # # from geometry_msgs.msg import Twist
# # # from std_msgs.msg import Float32

# # # from pynput import keyboard


# # # class Controller(Node):

# # #     def __init__(self):
# # #         super().__init__('controller')

# # #         self.get_logger().info('Controller Node has been started.')


# # #         self.declare_parameter('velocity', '/cmd_vel')
# # #         self.declare_parameter(
# # #             'ultrasonic_topic',
# # #             '/ultrasonic_distance'
# # #         )

# # #         self.declare_parameter('control_loop_period', 0.05)

# # #         self.declare_parameter('max_linear_speed', 0.5)
# # #         self.declare_parameter('max_angular_speed', 0.5)

# # #         # Field dimensions
# # #         self.declare_parameter('field_length', 3.0)
# # #         self.declare_parameter('field_width', 1.5)

# # #         # Safe distance from wall
# # #         self.declare_parameter('wall_distance', 0.30)
# # #         self.declare_parameter('wall_tolerance', 0.05)

# # #         # Initial diagonal movement
# # #         self.declare_parameter('move_time', 2.0)

# # #         # Rotation calibration
# # #         self.declare_parameter('rotate_90_time', 1.5)
# # #         self.declare_parameter('rotate_180_time', 3.0)
# # #         self.declare_parameter('rotate_360_time', 6.0)

# # #         # Manual / Autonomous
# # #         # False = Manual
# # #         # True  = Autonomous
# # #         self.declare_parameter('state', False)


# # #         ultrasonic_topic = self.get_parameter(
# # #             'ultrasonic_topic'
# # #         ).value

# # #         self.cmd_vel = self.get_parameter(
# # #             'velocity'
# # #         ).value

# # #         self.control_period = self.get_parameter(
# # #             'control_loop_period'
# # #         ).value

# # #         self.max_linear_speed = self.get_parameter(
# # #             'max_linear_speed'
# # #         ).value

# # #         self.max_angular_speed = self.get_parameter(
# # #             'max_angular_speed'
# # #         ).value

# # #         self.field_length = self.get_parameter(
# # #             'field_length'
# # #         ).value

# # #         self.field_width = self.get_parameter(
# # #             'field_width'
# # #         ).value

# # #         self.wall_distance = self.get_parameter(
# # #             'wall_distance'
# # #         ).value

# # #         self.wall_tolerance = self.get_parameter(
# # #             'wall_tolerance'
# # #         ).value

# # #         self.move_time = self.get_parameter(
# # #             'move_time'
# # #         ).value

# # #         self.rotate_90_time = self.get_parameter(
# # #             'rotate_90_time'
# # #         ).value

# # #         self.rotate_180_time = self.get_parameter(
# # #             'rotate_180_time'
# # #         ).value

# # #         self.rotate_360_time = self.get_parameter(
# # #             'rotate_360_time'
# # #         ).value

# # #         self.state = self.get_parameter(
# # #             'state'
# # #         ).value

# # #         self.vel_publisher = self.create_publisher(
# # #             Twist,
# # #             self.cmd_vel,
# # #             10
# # #         )

# # #         self.ultrasonic_subscriber = self.create_subscription(
# # #             Float32,
# # #             ultrasonic_topic,
# # #             self.ultrasonic_callback,
# # #             10
# # #         )

# # #         self.linear_vel_X = 0.0
# # #         self.linear_vel_Y = 0.0
# # #         self.angular_vel = 0.0

# # #         self.ultrasonic_distance = None

# # #         # Store ultrasonic readings
# # #         self.ultrasonic_readings = []


# # #         self.auto_state = 'IDLE'

# # #         self.state_start_time = None

# # #         # Estimated position
# # #         self.robot_x = None
# # #         self.robot_y = None

# # #         # Position before moving in Y
# # #         self.start_y = None


# # #         self.listener = keyboard.Listener(
# # #             on_press=self.on_press,
# # #             on_release=self.on_release
# # #         )

# # #         self.listener.start()

# # #         self.timer = self.create_timer(
# # #             self.control_period,
# # #             self.publish_velocity
# # #         )

# # #     def on_press(self, key):

# # #         try:

# # #             # Do not allow manual movement while autonomous
# # #             if self.state:
# # #                 if key == keyboard.Key.space:
# # #                     self.state = False
# # #                     self.auto_state = 'IDLE'

# # #                     self.get_logger().info('AUTONOMOUS STOPPED -> MANUAL MODE')

# # #                 return

# # #             if key == keyboard.Key.up:
# # #                 self.moveForward()

# # #             elif key == keyboard.Key.down:
# # #                 self.moveBackward()

# # #             elif key == keyboard.Key.left:
# # #                 self.moveLeft()

# # #             elif key == keyboard.Key.right:
# # #                 self.moveRight()

# # #             elif hasattr(key, 'char') and key.char == 'a':
# # #                 self.turnLeft()

# # #             elif hasattr(key, 'char') and key.char == 'd':
# # #                 self.turnRight()

# # #             elif key == keyboard.Key.space:

# # #                 self.state = True

# # #                 self.get_logger().info(
# # #                     'AUTONOMOUS MODE'
# # #                 )

# # #                 # Start autonomous sequence
# # #                 self.auto_state = 'START'

# # #                 self.state_start_time = time.time()

# # #                 # Clear old ultrasonic readings
# # #                 self.ultrasonic_readings.clear()

# # #                 self.robot_x = None
# # #                 self.robot_y = None

# # #         except AttributeError:
# # #             pass

# # #     def on_release(self, key):

# # #         try:

# # #             if (
# # #                 key == keyboard.Key.up
# # #                 or key == keyboard.Key.down
# # #             ):
# # #                 self.linear_vel_X = 0.0

# # #             elif (
# # #                 key == keyboard.Key.left
# # #                 or key == keyboard.Key.right
# # #             ):
# # #                 self.linear_vel_Y = 0.0

# # #             elif (
# # #                 hasattr(key, 'char')
# # #                 and key.char in ['a', 'd']
# # #             ):
# # #                 self.angular_vel = 0.0

# # #         except AttributeError:
# # #             pass

# # #     def ultrasonic_callback(self, msg):

# # #         self.ultrasonic_distance = msg.data

# # #         if self.state and self.auto_state == 'READ_ULTRASONIC':

# # #             self.ultrasonic_readings.append(self.ultrasonic_distance)

# # #     def moveForward(self):

# # #         self.linear_vel_X = self.max_linear_speed

# # #     def moveBackward(self):

# # #         self.linear_vel_X = -self.max_linear_speed

# # #     def moveLeft(self):

# # #         self.linear_vel_Y = self.max_linear_speed

# # #     def moveRight(self):

# # #         self.linear_vel_Y = -self.max_linear_speed

# # #     def turnLeft(self):

# # #         self.angular_vel = self.max_angular_speed

# # #     def turnRight(self):

# # #         self.angular_vel = -self.max_angular_speed

# # #     def autonomous(self):

# # #         msg = Twist()

# # #         if self.auto_state == 'START':

# # #             self.get_logger().info(
# # #                 'AUTO: Starting sequence'
# # #             )

# # #             self.get_logger().info(
# # #                 'AUTO: Moving diagonally...'
# # #             )

# # #             self.state_start_time = time.time()

# # #             self.auto_state = 'MOVE_DIAGONAL'


# # #         elif self.auto_state == 'MOVE_DIAGONAL':

# # #             # Diagonal movement
# # #             msg.linear.x = self.max_linear_speed
# # #             msg.linear.y = self.max_linear_speed

# # #             msg.angular.z = 0.0

# # #             elapsed = time.time() - self.state_start_time

# # #             if elapsed >= self.move_time:

# # #                 msg.linear.x = 0.0
# # #                 msg.linear.y = 0.0

# # #                 self.get_logger().info(
# # #                     'AUTO: Diagonal movement finished'
# # #                 )

# # #                 self.get_logger().info(
# # #                     'AUTO: Starting 360-degree calibration'
# # #                 )

# # #                 self.state_start_time = time.time()

# # #                 self.auto_state = 'ROTATE_360'

# # #         elif self.auto_state == 'ROTATE_360':

# # #             msg.linear.x = 0.0
# # #             msg.linear.y = 0.0

# # #             msg.angular.z = self.max_angular_speed

# # #             elapsed = time.time() - self.state_start_time

# # #             if elapsed >= self.rotate_360_time:

# # #                 msg.angular.z = 0.0

# # #                 self.get_logger().info(
# # #                     'AUTO: 360-degree calibration finished'
# # #                 )

# # #                 # Start reading ultrasonic
# # #                 self.ultrasonic_readings.clear()

# # #                 self.auto_state = 'READ_ULTRASONIC'

# # #         elif self.auto_state == 'READ_ULTRASONIC':

# # #             msg.linear.x = 0.0
# # #             msg.linear.y = 0.0
# # #             msg.angular.z = 0.0

            
# # #             if not hasattr(self, 'ultrasonic_read_start'):

# # #                 self.ultrasonic_read_start = time.time()

# # #             elapsed = (time.time()- self.ultrasonic_read_start)

# # #             if elapsed >= 1.0:

# # #                 if len(self.ultrasonic_readings) > 0:

# # #                     average_distance = (sum(self.ultrasonic_readings)/ len(self.ultrasonic_readings))

# # #                     self.get_logger().info('AUTO: Ultrasonic readings collected')

# # #                     self.get_logger().info(f'Number of readings: 'f'{len(self.ultrasonic_readings)}')

# # #                     self.get_logger().info(f'Average distance: 'f'{average_distance:.2f} m')

# # #                     self.get_logger().info(f'Readings: 'f'{self.ultrasonic_readings}')

# # #                     self.robot_x = average_distance

# # #                 else:

# # #                     self.get_logger().warn(
# # #                         'AUTO: No ultrasonic readings'
# # #                     )

# # #                 del self.ultrasonic_read_start

# # #                 self.get_logger().info(
# # #                     'AUTO: Rotating 90 degrees'
# # #                 )

# # #                 self.state_start_time = time.time()

# # #                 self.auto_state = 'ROTATE_90'

# # #         elif self.auto_state == 'ROTATE_90':

# # #             msg.linear.x = 0.0
# # #             msg.linear.y = 0.0

# # #             msg.angular.z = self.max_angular_speed

# # #             elapsed = time.time() - self.state_start_time

# # #             if elapsed >= self.rotate_90_time:

# # #                 msg.angular.z = 0.0

# # #                 self.get_logger().info(
# # #                     'AUTO: 90-degree rotation finished'
# # #                 )
# # #                 self.robot_y = 0.0
# # #                 self.start_y = self.robot_y

# # #                 self.get_logger().info(
# # #                     f'AUTO: Starting Y movement'
# # #                 )

# # #                 self.auto_state = 'MOVE_Y'

# # #         elif self.auto_state == 'MOVE_Y':

# # #             msg.linear.x = 0.0
# # #             msg.angular.z = 0.0

# # #             min_y = self.wall_distance

# # #             max_y = (
# # #                 self.field_width
# # #                 - self.wall_distance
# # #             )

# # #             if self.ultrasonic_distance is not None:

# # #                 distance = self.ultrasonic_distance

# # #                 estimated_y = distance

# # #                 self.robot_y = estimated_y

# # #                 self.get_logger().info(f'AUTO: Y position = 'f'{self.robot_y:.2f} m')


# # #                 if self.robot_y <= min_y:

# # #                     msg.linear.y = 0.0

# # #                     self.get_logger().info('AUTO: Reached minimum Y constraint')

# # #                     self.auto_state = 'DONE'


# # #                 elif self.robot_y >= max_y:

# # #                     msg.linear.y = 0.0

# # #                     self.get_logger().info('AUTO: Reached maximum Y constraint')

# # #                     self.auto_state = 'DONE'

# # #                 else:

# # #                     msg.linear.y = self.max_linear_speed

# # #             else:

# # #                 msg.linear.y = 0.0

# # #                 self.get_logger().warn(
# # #                     'AUTO: Ultrasonic unavailable - STOP'
# # #                 )
# # #         elif self.auto_state == 'DONE':

# # #             msg.linear.x = 0.0
# # #             msg.linear.y = 0.0
# # #             msg.angular.z = 0.0

# # #             self.get_logger().info('AUTO: Sequence finished')


# # #         else:

# # #             msg.linear.x = 0.0
# # #             msg.linear.y = 0.0
# # #             msg.angular.z = 0.0

# # #         return msg


# # #     def publish_velocity(self):

# # #         if not self.state:


# # #             msg = Twist()

# # #             msg.linear.x = self.linear_vel_X
# # #             msg.linear.y = self.linear_vel_Y
# # #             msg.angular.z = self.angular_vel

# # #         else:

# # #             msg = self.autonomous()

# # #         self.vel_publisher.publish(msg)


# # # def main(args=None):

# # #     rclpy.init(args=args)

# # #     controller = Controller()

# # #     try:

# # #         rclpy.spin(controller)

# # #     except KeyboardInterrupt:

# # #         pass

# # #     finally:

# # #         # Stop robot
# # #         msg = Twist()

# # #         controller.vel_publisher.publish(msg)

# # #         controller.listener.stop()

# # #         controller.destroy_node()

# # #         rclpy.shutdown()


# # # if __name__ == '__main__':

# # #     main()


# # #!/usr/bin/env python3
# # import rclpy
# # import time
# # from rclpy.node import Node
# # from geometry_msgs.msg import Twist
# # from std_msgs.msg import Float32
# # from pynput import keyboard


# # class Controller(Node):

# #     def __init__(self):
# #         super().__init__('controller')

# #         self.get_logger().info('Controller Node has been started.')

# #         self.declare_parameter('velocity', '/cmd_vel')
# #         self.declare_parameter('ultrasonic_topic', '/ultrasonic_distance')
# #         self.declare_parameter('detection_max_range',3.0)     # Object detected
# #         self.declare_parameter('clear_margin', 0.15) 
        
# #         self.declare_parameter('control_loop_period', 0.05)
        
# #         self.declare_parameter('max_linear_speed', 10.0)
# #         self.declare_parameter('max_angular_speed', 5.0)

# #         self.declare_parameter('wall_distance', 0.30)
# #         self.declare_parameter('wall_tolerance', 0.05)

# #         self.declare_parameter('move_time', 2.0)
# #         self.declare_parameter('rotate_90_time', 1.5)
# #         self.declare_parameter('rotate_180_time', 3.0)
# #         self.declare_parameter('rotate_360_time', 6.0)
# #         # Manual / Autonomous mode
# #         # False = Manual
# #         # True  = Autonomous
# #         self.declare_parameter('state', False)

# #         ultrasonic_topic = self.get_parameter('ultrasonic_topic').get_parameter_value().string_value

# #         self.cmd_vel = self.get_parameter('velocity').get_parameter_value().string_value

# #         self.control_period = self.get_parameter('control_loop_period').value

# #         self.max_linear_speed = self.get_parameter('max_linear_speed').value

# #         self.max_angular_speed = self.get_parameter('max_angular_speed').value

# #         self.state = self.get_parameter('state').value

# #         self.wall_distance = self.get_parameter('wall_distance').value

# #         self.wall_tolerance = self.get_parameter('wall_tolerance').value

# #         self.rotate_90_time = self.get_parameter('rotate_90_time').value
# #         self.rotate_180_time = self.get_parameter('rotate_180_time').value
# #         self.rotate_360_time = self.get_parameter('rotate_360_time').value

# #         self.vel_publisher = self.create_publisher(Twist,self.cmd_vel,10)
# #         self.ultrasonic_subscriber = self.create_subscription(Float32,ultrasonic_topic,self.ultrasonic_callback,10)
        
# #         self.linear_vel_X = 0.0
# #         self.linear_vel_Y = 0.0
# #         self.angular_vel = 0.0

# #         self.ultrasonic_distance = None

# #         self.listener = keyboard.Listener(on_press=self.on_press, on_release=self.on_release)

# #         self.listener.start()

# #         self.timer = self.create_timer(self.control_period,self.publish_velocity)

# #     def on_press(self, key):

# #         try:
# #             if key == keyboard.Key.up:
# #                 self.moveForward()
# #             elif key == keyboard.Key.down:
# #                 self.moveBackward()

# #             elif key == keyboard.Key.left:
# #                 self.moveLeft()
# #             elif key == keyboard.Key.right:
# #                 self.moveRight()

# #             elif hasattr(key, 'char') and key.char == 'a':
# #                 self.turnLeft()
# #             elif hasattr(key, 'char') and key.char == 'd':
# #                 self.turnRight()

# #             elif key == keyboard.Key.space:
# #                 self.state = not self.state
# #                 if self.state:
# #                     self.get_logger().info('AUTONOMOUS MODE')

# #                     # self.auto_state = 'START'
# #                     # self.state_start_time = time.time()
# #                 else:
# #                     self.get_logger().info('MANUAL MODE')

# #         except AttributeError:
# #             pass

# #     def on_release(self, key):
# #         try:
# #             if (key == keyboard.Key.up or key == keyboard.Key.down):
# #                 self.linear_vel_X = 0.0

# #             elif (key == keyboard.Key.left or key == keyboard.Key.right):
# #                 self.linear_vel_Y = 0.0

# #             elif (hasattr(key, 'char') and key.char in ['a', 'd']):
# #                 self.angular_vel = 0.0

# #         except AttributeError:
# #             pass

# #     def ultrasonic_callback(self, msg):
# #         self.ultrasonic_distance = msg.data
# #         self.get_logger().info(f'Ultrasonic Distance: {self.ultrasonic_distance:.2f} m')

# #     def moveForward(self):
# #         self.linear_vel_X = self.max_linear_speed

# #     def moveBackward(self):
# #         self.linear_vel_X = -self.max_linear_speed

# #     def moveLeft(self):
# #         self.linear_vel_Y = self.max_linear_speed

# #     def moveRight(self):
# #         self.linear_vel_Y = -self.max_linear_speed

# #     def turnLeft(self):
# #         self.angular_vel = self.max_angular_speed

# #     def turnRight(self):
# #         self.angular_vel = -self.max_angular_speed

# #     def autonomous(self, msg):
# #         # This function is a placeholder for the autonomous controller logic.
# #         # You can implement your autonomous control logic here.
# #         msg = Twist()

# #         if self.auto_state == 'START':

# #             msg.linear.x = self.max_linear_speed
# #             msg.linear.y = self.max_linear_speed
# #             msg.angular.z = 0.0

# #             if (time.time() - self.state_start_time) >= self.move_time:
# #                 msg.linear.x = 0.0
# #                 msg.linear.y = 0.0

# #             self.get_logger().info(
# #                 'AUTO: moving to calibrate'
# #             )

# #             self.auto_state = 'ROTATE_360'

# #         elif self.auto_state == 'ROTATE_360':
# #             msg.linear.x = 0.0
# #             msg.linear.y = 0.0
# #             msg.angular.z = self.max_angular_speed

# #             if (time.time() - self.state_start_time) >= self.rotate_360_time:
# #                 msg.angular.z = 0.0
# #                 self.get_logger().info(
# #                     'AUTO: calibration done'
# #                 )
# #                 self.auto_state = ''
# #                 self.state_start_time = time.time()

# #         elif self.auto_state == 'ROTATE_360':
# #             msg.linear.x = 0.0
# #             msg.linear.y = 0.0
# #             msg.angular.z = self.max_angular_speed
            
# #             if (time.time() - self.state_start_time) >= self.rotate_360_time:
# #                 msg.angular.z = 0.0
# #                 self.get_logger().info(
# #                     'AUTO: calibration done'
# #                 )
# #                 self.auto_state = ''
# #                 self.state_start_time = time.time()


# #         elif self.auto_state == 'ROTATE_180':
# #             msg.linear.x = 0.0
# #             msg.linear.y = 0.0
# #             msg.angular.z = self.max_angular_speed

# #             if (time.time() - self.state_start_time) >= self.rotate_180_time:
# #                 msg.angular.z = 0.0
# #                 self.get_logger().info(
# #                     'AUTO: Completed 180-degree rotation.'
# #                 )
# #                 self.auto_state = 'MOVE_TO_WALL'
# #                 self.state_start_time = time.time()




        

# #         # elif self.auto_state == 'MOVE_TO_WALL':
# #         #     if self.ultrasonic_distance is not None and self.ultrasonic_distance > self.wall_distance + self.wall_tolerance:
# #         #         msg.linear.x = self.max_linear_speed
# #         #         msg.linear.y = 0.0
# #         #         msg.angular.z = 0.0
# #         #     else:
# #         #         msg.linear.x = 0.0
# #         #         msg.linear.y = 0.0
# #         #         msg.angular.z = 0.0

# #         #         self.get_logger().info(
# #         #             'AUTO: Reached wall.'
# #         #         )

# #         #         self.auto_state = 'TURN_LEFT'

        
# #         self.turnLeft()
        
    
# #     def publish_velocity(self):
# #         msg = Twist()

# #         if not self.state:

# #             msg.linear.x = self.linear_vel_X
# #             msg.linear.y = self.linear_vel_Y
# #             msg.angular.z = self.angular_vel

# #         else:
# #             # leave it for the autonomous controller to handle the velocity commands later
# #             self.autonomous(msg)

# #         self.vel_publisher.publish(msg)

# # def main(args=None):

# #     rclpy.init(args=args)
# #     controller = Controller()

# #     try:
# #         rclpy.spin(controller)
# #     except KeyboardInterrupt:
# #         pass

# #     finally:
# #         # Stop robot before shutting down
# #         msg = Twist()
# #         controller.vel_publisher.publish(msg)
# #         controller.listener.stop()
# #         controller.destroy_node()
# #         rclpy.shutdown()


# # if __name__ == '__main__':

# #     main()


# #!/usr/bin/env python3

# import time
# import rclpy

# from rclpy.node import Node
# from geometry_msgs.msg import Twist
# from std_msgs.msg import Bool
# from pynput import keyboard


# class Controller(Node):
#     def __init__(self):
#         super().__init__('controller')

#         self.get_logger().info('Controller Node has been started.')

#         self.declare_parameter('velocity', '/cmd_vel')
#         self.declare_parameter('camera_state_topic', '/camera_state')
#         self.declare_parameter('control_loop_period', 0.05)

#         self.declare_parameter('max_linear_speed', 0.3)
#         self.declare_parameter('max_angular_speed', 0.5)

#         self.declare_parameter('move_time', 2.0)
#         self.declare_parameter('rotate_90_time', 1.5)
#         self.declare_parameter('rotate_180_time', 3.0)
#         self.declare_parameter('rotate_360_time', 6.0)

#         self.cmd_vel = self.get_parameter('velocity').value
#         self.camera_topic = self.get_parameter('camera_state_topic').value
#         self.control_period = self.get_parameter('control_loop_period').value

#         self.max_linear_speed = self.get_parameter('max_linear_speed').value
#         self.max_angular_speed = self.get_parameter('max_angular_speed').value

#         self.move_time = self.get_parameter('move_time').value
#         self.rotate_90_time = self.get_parameter('rotate_90_time').value
#         self.rotate_180_time = self.get_parameter('rotate_180_time').value
#         self.rotate_360_time = self.get_parameter('rotate_360_time').value

#         self.vel_publisher = self.create_publisher(
#             Twist,
#             self.cmd_vel,
#             10
#         )

#         self.camera_subscriber = self.create_subscription(
#             Bool,
#             self.camera_topic,
#             self.camera_state_callback,
#             10
#         )

#         self.linear_vel_X = 0.0
#         self.linear_vel_Y = 0.0
#         self.angular_vel = 0.0

#         self.camera_detected = False
#         self.detected_scrolls = 0

#         # False = Manual
#         # True = Autonomous
#         self.state = False

#         self.auto_state = 'IDLE'
#         self.state_start_time = time.time()

#         self.listener = keyboard.Listener(
#             on_press=self.on_press,
#             on_release=self.on_release
#         )
#         self.listener.start()

#         self.timer = self.create_timer(
#             self.control_period,
#             self.publish_velocity
#         )

#     def on_press(self, key):
#         try:
#             if key == keyboard.Key.up:
#                 self.moveForward()

#             elif key == keyboard.Key.down:
#                 self.moveBackward()

#             elif key == keyboard.Key.left:
#                 self.moveLeft()

#             elif key == keyboard.Key.right:
#                 self.moveRight()

#             elif hasattr(key, 'char') and key.char == 'a':
#                 self.turnLeft()

#             elif hasattr(key, 'char') and key.char == 'd':
#                 self.turnRight()

#             elif key == keyboard.Key.space:
#                 self.state = not self.state

#                 if self.state:
#                     self.start_autonomous()
#                 else:
#                     self.stop_autonomous()

#         except AttributeError:
#             pass

#     def on_release(self, key):
#         try:
#             if key == keyboard.Key.up or key == keyboard.Key.down:
#                 self.linear_vel_X = 0.0

#             elif key == keyboard.Key.left or key == keyboard.Key.right:
#                 self.linear_vel_Y = 0.0

#             elif hasattr(key, 'char') and key.char in ['a', 'd']:
#                 self.angular_vel = 0.0

#         except AttributeError:
#             pass

#     def camera_state_callback(self, msg):
#         self.camera_detected = msg.data

#     def moveForward(self):
#         self.linear_vel_X = self.max_linear_speed

#     def moveBackward(self):
#         self.linear_vel_X = -self.max_linear_speed

#     def moveLeft(self):
#         self.linear_vel_Y = self.max_linear_speed

#     def moveRight(self):
#         self.linear_vel_Y = -self.max_linear_speed

#     def turnLeft(self):
#         self.angular_vel = self.max_angular_speed

#     def turnRight(self):
#         self.angular_vel = -self.max_angular_speed

#     def start_autonomous(self):
#         self.detected_scrolls = 0
#         self.auto_state = 'START'
#         self.state_start_time = time.time()

#         self.linear_vel_X = 0.0
#         self.linear_vel_Y = 0.0
#         self.angular_vel = 0.0

#         self.get_logger().info('AUTONOMOUS MODE')

#     def stop_autonomous(self):
#         self.auto_state = 'IDLE'

#         self.linear_vel_X = 0.0
#         self.linear_vel_Y = 0.0
#         self.angular_vel = 0.0

#         self.get_logger().info('MANUAL MODE')

#     def autonomous(self):
#         msg = Twist()
#         elapsed = time.time() - self.state_start_time

#         if self.auto_state == 'START':
#             self.auto_state = 'MOVE_DIAGONAL'
#             self.state_start_time = time.time()
#             self.get_logger().info('AUTO: starting diagonal movement')

#         elif self.auto_state == 'MOVE_DIAGONAL':
#             msg.linear.x = self.max_linear_speed
#             msg.linear.y = self.max_linear_speed

#             if elapsed >= self.move_time:
#                 self.auto_state = 'ROTATE_360'
#                 self.state_start_time = time.time()
#                 self.get_logger().info('AUTO: rotating 360 degrees')

#         elif self.auto_state == 'ROTATE_360':
#             msg.angular.z = self.max_angular_speed

#             if elapsed >= self.rotate_360_time:
#                 self.auto_state = 'ROTATE_180'
#                 self.state_start_time = time.time()
#                 self.get_logger().info('AUTO: rotating 180 degrees')

#         elif self.auto_state == 'ROTATE_180':
#             msg.angular.z = self.max_angular_speed

#             if elapsed >= self.rotate_180_time:
#                 self.auto_state = 'ROTATE_90'
#                 self.state_start_time = time.time()
#                 self.get_logger().info('AUTO: rotating 90 degrees')

#         elif self.auto_state == 'ROTATE_90':
#             msg.angular.z = self.max_angular_speed

#             if elapsed >= self.rotate_90_time:
#                 self.auto_state = 'SEARCH'
#                 self.state_start_time = time.time()
#                 self.get_logger().info('AUTO: searching for scrolls')

#         elif self.auto_state == 'SEARCH':
#             msg.linear.x = self.max_linear_speed

#             if self.camera_detected:
#                 msg.linear.x = 0.0
#                 msg.linear.y = 0.0
#                 msg.angular.z = 0.0

#                 self.auto_state = 'SCROLL_DETECTED'
#                 self.state_start_time = time.time()

#                 self.get_logger().info('AUTO: scroll detected')

#             elif elapsed >= self.move_time:
#                 self.auto_state = 'SEARCH_ROTATE'
#                 self.state_start_time = time.time()

#         elif self.auto_state == 'SEARCH_ROTATE':
#             msg.angular.z = self.max_angular_speed

#             if self.camera_detected:
#                 msg.linear.x = 0.0
#                 msg.linear.y = 0.0
#                 msg.angular.z = 0.0

#                 self.auto_state = 'SCROLL_DETECTED'
#                 self.state_start_time = time.time()

#                 self.get_logger().info('AUTO: scroll detected')

#             elif elapsed >= self.rotate_90_time:
#                 self.auto_state = 'SEARCH'
#                 self.state_start_time = time.time()

#         elif self.auto_state == 'SCROLL_DETECTED':
#             msg.linear.x = 0.0
#             msg.linear.y = 0.0
#             msg.angular.z = 0.0

#             if not self.camera_detected:
#                 self.detected_scrolls += 1

#                 self.get_logger().info(
#                     f'Scroll completed: {self.detected_scrolls}/2'
#                 )

#                 if self.detected_scrolls >= 2:
#                     self.auto_state = 'DONE'
#                     self.get_logger().info('AUTO: two scrolls detected')

#                 else:
#                     self.auto_state = 'SEARCH'
#                     self.state_start_time = time.time()
#                     self.get_logger().info('AUTO: searching for next scroll')

#         elif self.auto_state == 'DONE':
#             msg.linear.x = 0.0
#             msg.linear.y = 0.0
#             msg.angular.z = 0.0

#         return msg

#     def publish_velocity(self):
#         if not self.state:
#             msg = Twist()

#             msg.linear.x = self.linear_vel_X
#             msg.linear.y = self.linear_vel_Y
#             msg.angular.z = self.angular_vel

#         else:
#             msg = self.autonomous()

#         self.vel_publisher.publish(msg)


# def main(args=None):
#     rclpy.init(args=args)

#     node = Controller()

#     try:
#         rclpy.spin(node)

#     except KeyboardInterrupt:
#         pass

#     finally:
#         node.listener.stop()
#         node.destroy_node()
#         rclpy.shutdown()


# if __name__ == '__main__':
#     main()


#!/usr/bin/env python3

import rclpy
import time

from rclpy.node import Node
from geometry_msgs.msg import Twist
from std_msgs.msg import Float32, Bool, Int32
from rclpy.parameter import Parameter
from rcl_interfaces.msg import SetParametersResult
from pynput import keyboard


class Controller(Node):

    def __init__(self):
        super().__init__('controller')

        self.get_logger().info('Controller Node has been started.')


        self.declare_parameter('velocity', '/cmd_vel')
        self.declare_parameter('ultrasonic_topic','/ultrasonic_distance')

        self.declare_parameter('camera_state_topic','/camera_state')
        self.declare_parameter('scroll_count_topic','/scroll_count')
        
        self.declare_parameter('control_loop_period', 0.05)

        self.declare_parameter('max_linear_speed', 8.0)
        self.declare_parameter('max_angular_speed', 3.0)

        # Field dimensions
        self.declare_parameter('field_length', 3.0)
        self.declare_parameter('field_width', 1.5)

        # Safe distance from wall
        self.declare_parameter('wall_distance', 0.30)
        self.declare_parameter('wall_tolerance', 0.05)

        # Initial diagonal movement
        self.declare_parameter('move_time', 3.0)
        self.declare_parameter('sweep_time', 6.0)

        # Rotation calibration
        self.declare_parameter('rotate_90_time', 1.28)
        self.declare_parameter('rotate_180_time', 3.0)
        self.declare_parameter('rotate_360_time', 6.0)

        # Manual / Autonomous
        # False = Manual
        # True  = Autonomous
        self.declare_parameter('state', False)
        self.declare_parameter('auto_state', 'IDLE')

        camera_state_topic = self.get_parameter('camera_state_topic').value
        scroll_count_topic = self.get_parameter('scroll_count_topic').value
        ultrasonic_topic = self.get_parameter('ultrasonic_topic').value
        self.cmd_vel = self.get_parameter('velocity').value
        self.control_period = self.get_parameter('control_loop_period').value
        self.max_linear_speed = self.get_parameter('max_linear_speed').value
        self.max_angular_speed = self.get_parameter('max_angular_speed').value
        self.field_length = self.get_parameter('field_length').value
        self.field_width = self.get_parameter('field_width').value
        self.wall_distance = self.get_parameter('wall_distance').value
        self.wall_tolerance = self.get_parameter('wall_tolerance').value
        self.move_time = self.get_parameter('move_time').value
        self.sweep_time = self.get_parameter('sweep_time').value
        self.rotate_90_time = self.get_parameter('rotate_90_time').value
        self.rotate_180_time = self.get_parameter('rotate_180_time').value
        self.rotate_360_time = self.get_parameter('rotate_360_time').value
        self.state = self.get_parameter('state').value
        self.auto_state = self.get_parameter('auto_state').value

        self.vel_publisher = self.create_publisher(Twist,self.cmd_vel,10)
        self.ultrasonic_subscriber = self.create_subscription(Float32,ultrasonic_topic,self.ultrasonic_callback,10)
        self.camera_state_subscriber = self.create_subscription(Bool,camera_state_topic,self.camera_state_callback,10)
        # self.scroll_count_subscriber = self.create_subscription(Int32,scroll_count_topic,self.scroll_count_callback,10)

        self.linear_vel_X = 0.0
        self.linear_vel_Y = 0.0
        self.angular_vel = 0.0

        self.ultrasonic_distance = None

        # Store ultrasonic readings
        self.ultrasonic_readings = []

        self.camera_detected = False

        self.state = False

        self.state_start_time = None

        # Estimated position
        self.robot_x = None
        self.robot_y = None

        # Position before moving in Y
        self.start_y = None


        self.listener = keyboard.Listener(
            on_press=self.on_press,
            on_release=self.on_release
        )

        self.listener.start()
        self.add_on_set_parameters_callback(self.parameter_callback)

        self.timer_vel = self.create_timer(self.control_period,self.publish_velocity)
    
    def on_press(self, key):

        try:

            # Do not allow manual movement while autonomous
            if self.state:
                if key == keyboard.Key.space:
                    self.state = False
                    self.auto_state = 'IDLE'

                    self.get_logger().info('AUTONOMOUS STOPPED -> MANUAL MODE')

                return

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

        
            # elif key == keyboard.Key.space:

            #     self.state = True

            #     self.get_logger().info('AUTONOMOUS MODE')

            #     # Start autonomous sequence
            #     self.auto_state = 'START'

            #     self.state_start_time = time.time()

            #     # Clear old ultrasonic readings
            #     self.ultrasonic_readings.clear()

            #     self.robot_x = None
            #     self.robot_y = None

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

    def parameter_callback(self, params):
        for param in params:
            if param.name == 'max_linear_speed':
                self.max_linear_speed = param.value
            elif param.name == 'max_angular_speed':
                self.max_angular_speed = param.value
            elif param.name == 'move_time':
                self.move_time = param.value
            elif param.name == 'sweep_time':
                self.sweep_time = param.value
            elif param.name == 'rotate_90_time':
                self.rotate_90_time = param.value
            elif param.name == 'rotate_180_time':
                self.rotate_180_time = param.value
            elif param.name == 'rotate_360_time':
                self.rotate_360_time = param.value
            elif param.name == 'state':
                self.state = param.value
            elif param.name == 'auto_state':
                self.auto_state = param.value


        return SetParametersResult(successful=True)
    
    def ultrasonic_callback(self, msg):

        self.ultrasonic_distance = msg.data

        if self.state and self.auto_state == 'READ_ULTRASONIC':

            self.ultrasonic_readings.append(self.ultrasonic_distance)

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

    def camera_state_callback(self, msg):

        old_state = self.camera_detected

        self.camera_detected = msg.data

        if self.camera_detected and not old_state:
            self.get_logger().info('CAMERA: Scroll detected!')

        elif not self.camera_detected and old_state:
            self.get_logger().info('CAMERA: Detection finished.')

    # def scroll_count_callback(self, msg):
    #     self.scroll_count = msg.data

        self.get_logger().info(f'CAMERA: Scroll count = 'f'{self.scroll_count}')

    def start_autonomous(self):
        self.detected_scrolls = 0
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
        sweep_speed = self.max_linear_speed - 1.0
        elapsed = time.time() - self.state_start_time

        self.camera_detected = False

        if self.auto_state == 'START':

            self.get_logger().info('AUTO: Starting sequence')
            self.get_logger().info('AUTO: Moving diagonally...')

            self.state_start_time = time.time()

            self.auto_state = 'MOVE_DIAGONAL'


        elif self.auto_state == 'MOVE_DIAGONAL':

            # Diagonal movement
            msg.linear.x = self.max_linear_speed
            msg.linear.y = -(self.max_linear_speed - 1.0)

            msg.angular.z = 0.0

            if elapsed >= self.move_time:

                msg.linear.x = 0.0
                msg.linear.y = 0.0

                self.get_logger().info('AUTO: Diagonal movement finished')
                self.get_logger().info('AUTO: Starting 360-degree calibration')

                self.state_start_time = time.time()

                self.auto_state = 'ROTATE_90'

        # elif self.auto_state == 'ROTATE_360':

        #     msg.linear.x = 0.0
        #     msg.linear.y = 0.0

        #     msg.angular.z = self.max_angular_speed

        #     elapsed = time.time() - self.state_start_time

        #     if elapsed >= self.rotate_360_time:

        #         msg.angular.z = 0.0

        #         self.get_logger().info('AUTO: 360-degree calibration finished')
        #         self.state_start_time = time.time()
        #         # Start reading ultrasonic
        #         # self.ultrasonic_readings.clear()

        #         # self.auto_state = 'READ_ULTRASONIC'
        #         self.auto_state = 'ROTATE_90'

        

        elif self.auto_state == 'ROTATE_90':

            msg.linear.x = 0.0
            msg.linear.y = 0.0

            msg.angular.z = self.max_angular_speed

            if elapsed >= self.rotate_90_time:
                self.state_start_time = time.time()
                msg.angular.z = 0.0

                self.get_logger().info('AUTO: 90-degree rotation finished')

                # self.robot_y = 0.0
                # self.start_y = self.robot_y

                self.get_logger().info(f'AUTO: Starting Y movement')

                self.auto_state = 'MOVE_Y'

        elif self.auto_state == 'MOVE_Y':
            msg.angular.z = 0.0
            msg.linear.x = 0.0
            msg.linear.y = - sweep_speed

            if elapsed >= (self.move_time - 2.3):
            
                msg.linear.y = 0.0
                self.state_start_time = time.time()
                self.get_logger().info('move_y finished to the end of the field on right')

                self.get_logger().info(f'AUTO: Starting Y movement')

                self.auto_state = 'sweep'

        elif self.auto_state == 'sweep' :
            msg.angular.z = 0.0
            msg.linear.x = 0.0
        
            # if self.auto_state == 'SCROLL_DETECTED':
            #     msg.linear.x = 0.0
            #     msg.linear.y = 0.0
            #     msg.angular.z = 0.0
            #     self.get_logger().info('AUTO: ROBOT STOPPED FOR SCROLL')
                
            #     # Wait here until camera says detection
            #     # has finished.
    
            #     if not self.camera_detected:
    
            #         self.get_logger().info('AUTO: Scroll processing finished')
    
            #         if self.scroll_count >= 2:
            #             self.auto_state = 'DONE'
    
            #         else:
            #             self.get_logger().info('AUTO: Searching for next scroll')
            #             self.auto_state = 'sweep'

            msg.linear.y = sweep_speed

            if elapsed >= (self.sweep_time - 4.0):
                self.state_start_time = time.time()
                msg.linear.y = 0.0
                self.get_logger().info('move_y finished to the end of the field on left')

            msg.linear.y = - sweep_speed

            if elapsed >= (self.sweep_time - 4.0):
                self.state_start_time = time.time()
                msg.linear.y = 0.0
                self.get_logger().info('move_y finished to the end of the field on right')

        elif self.auto_state == 'SCROLL_DETECTED':

            # STOP
            msg.linear.x = 0.0
            msg.linear.y = 0.0
            msg.angular.z = 0.0

            self.get_logger().info('AUTO: ROBOT STOPPED FOR SCROLL')

            # Wait here until camera says detection
            # has finished.

            if not self.camera_detected:

                self.get_logger().info('AUTO: Scroll processing finished')

                if self.scroll_count >= 2:
                    self.get_logger().info('AUTO: TWO SCROLLS DETECTED')
                    self.auto_state = 'DONE'

                else:
                    self.get_logger().info('AUTO: Searching for next scroll')
                    self.auto_state = 'sweep'

        # elif self.auto_state == 'MOVE_Y':
        #     msg.linear.x = 0.0
        #     msg.angular.z = 0.0

        #     min_y = self.wall_distance

        #     max_y = (self.field_width - self.wall_distance)

        #     if self.ultrasonic_distance is not None:

        #         distance = self.ultrasonic_distance

        #         estimated_y = distance

        #         self.robot_y = estimated_y

        #         self.get_logger().info(f'AUTO: Y position = 'f'{self.robot_y:.2f} m')

        #         if self.robot_y <= min_y:

        #             msg.linear.y = 0.0

        #             self.get_logger().info('AUTO: Reached minimum Y constraint')

        #             self.auto_state = 'DONE'

        #         elif self.robot_y >= max_y:

        #             msg.linear.y = 0.0

        #             self.get_logger().info('AUTO: Reached maximum Y constraint')

        #             self.auto_state = 'DONE'

        #         else:
        #             msg.linear.y = self.max_linear_speed

        #     else:

        #         msg.linear.y = 0.0
        #         self.get_logger().warn('AUTO: Ultrasonic unavailable - STOP')
        # elif self.auto_state == 'READ_ULTRASONIC':

                #     msg.linear.x = 0.0
                #     msg.linear.y = 0.0
                #     msg.angular.z = 0.0

                    
                #     if not hasattr(self, 'ultrasonic_read_start'):

                #         self.ultrasonic_read_start = time.time()

                #     elapsed = (time.time()- self.ultrasonic_read_start)

                #     if elapsed >= 1.0:

                #         if len(self.ultrasonic_readings) > 0:

                #             average_distance = (sum(self.ultrasonic_readings)/ len(self.ultrasonic_readings))

                #             self.get_logger().info('AUTO: Ultrasonic readings collected')

                #             self.get_logger().info(f'Number of readings: 'f'{len(self.ultrasonic_readings)}')

                #             self.get_logger().info(f'Average distance: 'f'{average_distance:.2f} m')

                #             self.get_logger().info(f'Readings: 'f'{self.ultrasonic_readings}')

                #             self.robot_x = average_distance

                #         else:

                #             self.get_logger().warn('AUTO: No ultrasonic readings')

                #         del self.ultrasonic_read_start

                #         self.get_logger().info('AUTO: Rotating 90 degrees')

                #         self.state_start_time = time.time()

                #         self.auto_state = 'ROTATE_90'
        elif self.auto_state == 'DONE':

            msg.linear.x = 0.0
            msg.linear.y = 0.0
            msg.angular.z = 0.0

            self.get_logger().info('AUTO: Sequence finished')


        else:

            msg.linear.x = 0.0
            msg.linear.y = 0.0
            msg.angular.z = 0.0

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
    controller = Controller()

    try:

        rclpy.spin(controller)

    except KeyboardInterrupt:

        pass

    finally:

        # Stop robot
        msg = Twist()
        controller.vel_publisher.publish(msg)
        controller.listener.stop()
        controller.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()