cmake_minimum_required(VERSION 3.8)
project(robot_competition)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# Find dependencies
find_package(ament_cmake REQUIRED)
find_package(rclpy REQUIRED)
find_package(rosidl_default_generators REQUIRED)
find_package(action_msgs REQUIRED)

# Install Python scripts
install(PROGRAMS
  src/control.py
  DESTINATION lib/${PROJECT_NAME}
  RENAME controller_node
)
install(PROGRAMS
  src/scroll_detection_node.py
  DESTINATION lib/${PROJECT_NAME}
  RENAME camera_node
)

install(DIRECTORY launch
  DESTINATION share/${PROJECT_NAME}
)


if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  set(ament_cmake_copyright_FOUND TRUE)
  set(ament_cmake_cpplint_FOUND TRUE)
  ament_lint_auto_find_test_dependencies()
endif()

ament_package()