
from dobot_api import DobotApiDashboard, DobotApi, DobotApiMove
import time

def connect_robot():
    dashboard_ip = '192.168.250.101'
    dashboard_port = 29999
    move_ip = '192.168.250.101'
    move_port = 30003
    
    dashboard = DobotApiDashboard(dashboard_ip, dashboard_port)
    move = DobotApiMove(move_ip, move_port)
    return dashboard, move

def main():
    dashboard, move = connect_robot()
    
    # Activate the robot
    dashboard.EnableRobot()
    time.sleep(2)
    
    # Set speed to 100%
    dashboard.SpeedFactor(100)
    
    pos_object = [[291, 10, 12, 0], [272, 12, 12, 0], [255, 13.5, 12, 0], [237, 14, 12, 0], [290, -178, 12, 0], [271, -177, 12, 0], [252, -177, 12, 0], [233, -177, 12, 0]]
    pos_end = [158, 234, 36, 21]
    DO = 1
    
    k = 0
    while True:
        for i in range(len(pos_object)):
            k += 1
            # Move to 20 cm above the pick coordinate
            move.MovJ(pos_object[i][0], pos_object[i][1], pos_object[i][2] + 20, pos_object[i][3])
            move.Sync()
            
            # Move down 20 cm
            move.MovL(pos_object[i][0], pos_object[i][1], pos_object[i][2], pos_object[i][3])
            move.Sync()
            
            # Activate digital output
            dashboard.DO(DO, 1)
            time.sleep(0.5)
            
            # Ascend 20 cm
            move.MovL(pos_object[i][0], pos_object[i][1], pos_object[i][2] + 20, pos_object[i][3])
            move.Sync()
            
            # Move to 20 cm above the placement coordinate
            move.MovJ(pos_end[0], pos_end[1], pos_end[2] + 20, pos_end[3])
            move.Sync()
            
            # Move down 20 cm
            move.MovL(pos_end[0], pos_end[1], pos_end[2], pos_end[3])
            move.Sync()
            
            # Deactivate digital output
            dashboard.DO(DO, 0)
            time.sleep(0.5)
            
            # Ascend 20 cm
            move.MovL(pos_end[0], pos_end[1], pos_end[2] + 20, pos_end[3])
            move.Sync()
            
            print(f"[Task {k} completed]")
        
        k = 0
        print("[All tasks completed]")

if __name__ == "__main__":
    main()
