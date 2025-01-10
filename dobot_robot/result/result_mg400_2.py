
from dobot_api import DobotApiDashboard, DobotApi, DobotApiMove
import time

def connect_robot(ip):
    dashboard_p = DobotApiDashboard(ip, 29999)
    move_p = DobotApiMove(ip, 30003)
    feed_p = DobotApi(ip, 30004)
    return dashboard_p, move_p, feed_p

def move_to_position(move_p, position):
    move_p.MovJ(position[0], position[1], position[2], position[3])

def move_down_and_back(move_p, position, offset):
    move_p.MovL(position[0], position[1], position[2] - offset, position[3])
    time.sleep(1)  # Wait for the robot to move down
    move_p.MovL(position[0], position[1], position[2], position[3])
    time.sleep(1)  # Wait for the robot to move back

def main():
    ip = "192.168.250.101"
    pos_start = [284, 4, 90, -43]
    pos_end = [280, 104, 80, -23]
    offset = 10  # Offset in cm for the gripper movement

    dashboard_p, move_p, feed_p = connect_robot(ip)

    try:
        # Start the robot
        dashboard_p.EnableRobot()
        time.sleep(2)  # Wait for the robot to start

        while True:
            # Move to the start position
            move_to_position(move_p, pos_start)
            time.sleep(2)  # Wait for the robot to reach the start position

            # Move down to catch the object and then move back
            move_down_and_back(move_p, pos_start, offset)
            print("catch_ok")

            # Move to the end position
            move_to_position(move_p, pos_end)
            time.sleep(2)  # Wait for the robot to reach the end position

            # Move down to place the object and then move back
            move_down_and_back(move_p, pos_end, offset)
            print("place_ok")

    finally:
        # Stop the robot
        dashboard_p.DisableRobot()
        time.sleep(2)  # Wait for the robot to stop

if __name__ == "__main__":
    main()
