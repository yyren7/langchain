from dobot_api import DobotApiDashboard, DobotApi, DobotApiMove
import time


def connect_robot():
    ip = "192.168.250.101"
    dashboard_port = 29999
    move_port = 30003
    feed_port = 30004

    dashboard = DobotApiDashboard(ip, dashboard_port)
    move = DobotApiMove(ip, move_port)
    feed = DobotApi(ip, feed_port)

    return dashboard, move, feed


def pick_and_place(dashboard, move, feed, pos_pick, pos_end):
    k = 0
    while True:
        for group in pos_pick['groups']:
            for coord in group['coordinates']:
                k += 1
                x, y, z, r = int(coord['x']), int(coord['y']), int(coord['z']), int(coord['r'])

                # Move to 20 cm above the pick position
                move.MovL(x, y, z + 20, r)
                move.Sync()

                # Move down to the pick position
                move.MovL(x, y, z, r)
                move.Sync()

                # Activate the specified digital output
                dashboard.DO(1, 1)
                time.sleep(1)  # Ensure the gripper has time to activate

                # Move up 20 cm from the current position
                move.MovL(x, y, z + 20, r)
                move.Sync()

                # Move to 20 cm above the placement position
                move.MovL(pos_end[0], pos_end[1], pos_end[2] + 20, pos_end[3])
                move.Sync()

                # Move down to the placement position
                move.MovL(pos_end[0], pos_end[1], pos_end[2], pos_end[3])
                move.Sync()

                # Deactivate the specified digital output
                dashboard.DO(1, 0)
                time.sleep(1)  # Ensure the gripper has time to deactivate

                # Move up 20 cm from the current position
                move.MovL(pos_end[0], pos_end[1], pos_end[2] + 20, pos_end[3])
                move.Sync()

                print(f"[Task {k} completed]")

        k = 0
        print("[All tasks completed]")


if __name__ == "__main__":
    dashboard, move, feed = connect_robot()

    # Activate the robot
    dashboard.EnableRobot()
    time.sleep(2)

    # Set speed to 50%
    dashboard.SpeedFactor(50)

    pos_pick = {
        'groups': [
            {'name': 'first_group', 'coordinates': [
                {'number': '1', 'x': '298', 'y': '199', 'z': '14', 'r': '0'},
                {'number': '2', 'x': '278', 'y': '199', 'z': '14', 'r': '0'},
                {'number': '3', 'x': '258', 'y': '199', 'z': '14', 'r': '0'},
                {'number': '4', 'x': '238', 'y': '199', 'z': '14', 'r': '0'}
            ]},
            {'name': 'second_group', 'coordinates': [
                {'number': '1', 'x': '298', 'y': '179', 'z': '14', 'r': '0'},
                {'number': '2', 'x': '278', 'y': '179', 'z': '14', 'r': '0'},
                {'number': '3', 'x': '258', 'y': '179', 'z': '14', 'r': '0'},
                {'number': '4', 'x': '238', 'y': '179', 'z': '14', 'r': '0'}
            ]},
            {'name': 'third_group', 'coordinates': [
                {'number': '1', 'x': '298', 'y': '159', 'z': '14', 'r': '0'},
                {'number': '2', 'x': '278', 'y': '159', 'z': '14', 'r': '0'},
                {'number': '3', 'x': '258', 'y': '159', 'z': '14', 'r': '0'},
                {'number': '4', 'x': '238', 'y': '159', 'z': '14', 'r': '0'}
            ]}
        ]
    }

    pos_end = [192, 304, 80, 0]

    pick_and_place(dashboard, move, feed, pos_pick, pos_end)