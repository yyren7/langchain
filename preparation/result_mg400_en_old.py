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


def main():
    dashboard, move, feed = connect_robot()

    # Activate the robot
    dashboard.EnableRobot()
    time.sleep(2)

    # Set speed to 50%
    dashboard.SpeedFactor(50)

    pick_coordinates = [
        {'x': 298, 'y': 194, 'z': 17, 'r': 0},
        {'x': 273, 'y': 194, 'z': 17, 'r': 0},
        {'x': 248, 'y': 194, 'z': 17, 'r': 0},
        {'x': 298, 'y': 168, 'z': 17, 'r': 0},
        {'x': 273, 'y': 168, 'z': 17, 'r': 0},
        {'x': 248, 'y': 168, 'z': 17, 'r': 0},
        {'x': 298, 'y': 142, 'z': 17, 'r': 0},
        {'x': 273, 'y': 142, 'z': 17, 'r': 0},
        {'x': 248, 'y': 142, 'z': 17, 'r': 0},
        {'x': 298, 'y': 116, 'z': 17, 'r': 0},
        {'x': 273, 'y': 116, 'z': 17, 'r': 0},
        {'x': 248, 'y': 116, 'z': 17, 'r': 0}
    ]

    place_coordinates = [
        {'x': 242, 'y': 283, 'z': 35, 'r': 0},
        {'x': 217, 'y': 283, 'z': 35, 'r': 0},
        {'x': 192, 'y': 283, 'z': 35, 'r': 0},
        {'x': 167, 'y': 283, 'z': 35, 'r': 0},
        {'x': 242, 'y': 309, 'z': 35, 'r': 0},
        {'x': 217, 'y': 309, 'z': 35, 'r': 0},
        {'x': 192, 'y': 309, 'z': 35, 'r': 0},
        {'x': 167, 'y': 309, 'z': 35, 'r': 0},
        {'x': 242, 'y': 335, 'z': 35, 'r': 0},
        {'x': 217, 'y': 335, 'z': 35, 'r': 0},
        {'x': 192, 'y': 335, 'z': 35, 'r': 0},
        {'x': 167, 'y': 335, 'z': 35, 'r': 0}
    ]

    k = 0

    while True:
        for i in range(len(pick_coordinates)):
            k += 1

            # Move to 20 cm above pick coordinate
            move.MovJ(pick_coordinates[i]['x'], pick_coordinates[i]['y'], pick_coordinates[i]['z'] + 20,
                      pick_coordinates[i]['r'])
            move.Sync()

            # Move down to pick coordinate
            move.MovL(pick_coordinates[i]['x'], pick_coordinates[i]['y'], pick_coordinates[i]['z'],
                      pick_coordinates[i]['r'])
            move.Sync()

            # Activate digital output
            dashboard.DO(1, 1)
            time.sleep(0.5)

            # Move up 20 cm
            move.MovL(pick_coordinates[i]['x'], pick_coordinates[i]['y'], pick_coordinates[i]['z'] + 20,
                      pick_coordinates[i]['r'])
            move.Sync()

            # Move to 20 cm above place coordinate
            move.MovJ(place_coordinates[i]['x'], place_coordinates[i]['y'], place_coordinates[i]['z'] + 20,
                      place_coordinates[i]['r'])
            move.Sync()

            # Move down to place coordinate
            move.MovL(place_coordinates[i]['x'], place_coordinates[i]['y'], place_coordinates[i]['z'],
                      place_coordinates[i]['r'])
            move.Sync()

            # Deactivate digital output
            dashboard.DO(1, 0)
            time.sleep(0.5)

            # Move up 20 cm
            move.MovL(place_coordinates[i]['x'], place_coordinates[i]['y'], place_coordinates[i]['z'] + 20,
                      place_coordinates[i]['r'])
            move.Sync()

            print(f"[Task {k} completed]")

        k = 0
        print("[All tasks completed]")


if __name__ == "__main__":
    main()