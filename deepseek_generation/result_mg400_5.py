
from dobot_api import DobotApiDashboard, DobotApi, DobotApiMove
import time

def connect_robot():
    dashboard_p = DobotApiDashboard("192.168.250.101", 29999)
    move_p = DobotApiMove("192.168.250.101", 30003)
    feed_p = DobotApi("192.168.250.101", 30004)
    return dashboard_p, move_p, feed_p

def move_to_position(move_p, position):
    move_p.MovJ(position[0], position[1], position[2], position[3])

def move_down(move_p, position, distance):
    move_p.MovL(position[0], position[1], position[2] - distance, position[3])

def move_up(move_p, position, distance):
    move_p.MovL(position[0], position[1], position[2] + distance, position[3])

def set_digital_output(dashboard_p, do_index, state):
    dashboard_p.DO(do_index, state)

def main():
    dashboard_p, move_p, feed_p = connect_robot()
    dashboard_p.EnableRobot()
    time.sleep(2)

    pos_start = [[291, 10, 10, 0], [272, 12, 10, 0], [255, 13.5, 10, 0], [237, 14, 10, 0], [290, -178, 10, 0], [271, -177, 10, 0], [252, -177, 10, 0], [233, -177, 10, 0]]
    pos_end = [158, 234, 86, 21]
    DO = 1

    for _ in range(10):
        for start_pos in pos_start:
            # Move to the start position above 20cm
            move_to_position(move_p, [start_pos[0], start_pos[1], start_pos[2] + 20, start_pos[3]])
            time.sleep(0.1)

            # Move down 10cm to the actual start position
            move_down(move_p, start_pos, 20)
            time.sleep(0.1)

            # Activate the digital output
            set_digital_output(dashboard_p, DO, 1)
            time.sleep(0.1)

            # Move up 20cm
            move_up(move_p, start_pos, 20)
            time.sleep(0.1)

            # Move to the end position
            move_to_position(move_p, pos_end)
            time.sleep(0.1)

            # Deactivate the digital output
            set_digital_output(dashboard_p, DO, 0)
            time.sleep(0.1)

    dashboard_p.DisableRobot()
    return "任务完成"

if __name__ == "__main__":
    main()
