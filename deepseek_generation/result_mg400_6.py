from dobot_api import DobotApiDashboard, DobotApi, DobotApiMove
import time


def connect_robot():
    dashboard_p = DobotApiDashboard("192.168.250.101", 29999)
    move_p = DobotApiMove("192.168.250.101", 30003)
    feed_p = DobotApi("192.168.250.101", 30004)
    return dashboard_p, move_p, feed_p


def move_to_position(move_p, position):
    move_p.MovJ(position[0], position[1], position[2], position[3])


def move_down(move_p, current_position, distance):
    new_position = current_position[:]
    new_position[2] -= distance
    move_p.MovL(new_position[0], new_position[1], new_position[2], new_position[3])


def move_up(move_p, current_position, distance):
    new_position = current_position[:]
    new_position[2] += distance
    move_p.MovL(new_position[0], new_position[1], new_position[2], new_position[3])


def pick_and_place(dashboard_p, move_p, feed_p, pos_object, pos_end, DO):
    for pos in pos_object:
        # Calculate the start position above the object
        start_position = pos[:]
        start_position[2] += 20

        # Move to the start position
        move_to_position(move_p, start_position)
        time.sleep(0.1)

        # Move down to the object
        move_down(move_p, start_position, 20)
        time.sleep(0.1)

        # Activate the specified digital output
        dashboard_p.DO(DO, 1)
        time.sleep(0.1)

        # Move up from the object
        move_up(move_p, start_position, 20)
        time.sleep(0.1)

        # Move to the end position
        move_to_position(move_p, pos_end)
        time.sleep(0.1)

        # Deactivate the specified digital output
        dashboard_p.DO(DO, 0)
        time.sleep(0.1)

    return "任务完成"


if __name__ == "__main__":
    dashboard_p, move_p, feed_p = connect_robot()
    dashboard_p.EnableRobot()
    pos_object = [[291, 10, 10, 0], [272, 12, 10, 0], [255, 13.5, 10, 0], [237, 14, 10, 0], [290, -178, 10, 0],
                  [271, -177, 10, 0], [252, -177, 10, 0], [233, -177, 10, 0]]
    pos_end = [158, 234, 86, 21]
    DO = 1

    result = pick_and_place(dashboard_p, move_p, feed_p, pos_object, pos_end, DO)
    print(result)
