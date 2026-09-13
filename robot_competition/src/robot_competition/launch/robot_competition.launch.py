#!/usr/bin/env python3

from launch import LaunchDescription
from launch_ros.actions import Node
 
PACKAGE_NAME = 'robot_competition'
CAMERA_EXECUTABLE = 'camera_node'          
CONTROLLER_EXECUTABLE = 'controller_node'  
DEBUG_IMAGE_TOPIC = '/scroll_detection/debug_image'
 
 
def generate_launch_description():
    return LaunchDescription([
        Node(
            package=PACKAGE_NAME,
            executable=CAMERA_EXECUTABLE,
            name='scroll_detection_node',
            output='screen',
        ),
        Node(
            package=PACKAGE_NAME,
            executable=CONTROLLER_EXECUTABLE,
            name='controller',
            output='screen',
        ),
        Node(
            package='rqt_image_view',
            executable='rqt_image_view',
            name='scroll_debug_view',
            arguments=[DEBUG_IMAGE_TOPIC],
            output='screen',
        ),
    ])