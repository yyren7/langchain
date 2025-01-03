
import json
import time
from dobot_api import DobotApiDashboard, DobotApi, DobotApiMove

def connect_robot():
    ip = "192.168.250.101"
    dashboard_port = 29999
    move_port = 30003
    feed_port = 30004
    
    dashboard = DobotApiDashboard(ip, dashboard_port)
    move = DobotApiMove(ip, move_port)
    feed = DobotApi(ip, feed_port)
    
    return dashboard, move, feed

def load_points(file_path):
    with open(file_path, 'r') as file:
        data = json.load(file)
    return data['groups']

def move_to_position(move, x, y, z, r):
    move.MovL(x, y, z, r)
    move.Sync()

def activate_digital_output(dashboard, do_index):
    dashboard.DO(do_index, 1)
    time.sleep(0.2)

def deactivate_digital_output(dashboard, do_index):
    dashboard.DO(do_index, 0)
    time.sleep(0.2)

def main():
    dashboard, move, feed = connect_robot()
    
    # Activate the robot
    dashboard.EnableRobot()
    time.sleep(2)
    
    # Set speed to 50%
    dashboard.SpeedFactor(50)
    
    points = load_points('./generated_points.json')
    
    pick_points = points[0]['coordinates']
    place_points = points[1]['coordinates']
    
    do_index = 1  # Digital output index
    
    while True:
        for i in range(len(pick_points)):
            pick_point = pick_points[i]
            place_point = place_points[i]
            
            # Move to 40 cm above pick point
            move_to_position(move, float(pick_point['x']), float(pick_point['y']), float(pick_point['z']) + 40, float(pick_point['r']))
            
            # Move down to pick point
            move_to_position(move, float(pick_point['x']), float(pick_point['y']), float(pick_point['z']), float(pick_point['r']))
            
            # Activate DO and wait
            activate_digital_output(dashboard, do_index)
            
            # Move up 40 cm
            move_to_position(move, float(pick_point['x']), float(pick_point['y']), float(pick_point['z']) + 40, float(pick_point['r']))
            
            # Move to 40 cm above place point
            move_to_position(move, float(place_point['x']), float(place_point['y']), float(place_point['z']) + 40, float(place_point['r']))
            
            # Move down to place point
            move_to_position(move, float(place_point['x']), float(place_point['y']), float(place_point['z']), float(place_point['r']))
            
            # Deactivate DO and wait
            deactivate_digital_output(dashboard, do_index)
            
            # Move up 40 cm
            move_to_position(move, float(place_point['x']), float(place_point['y']), float(place_point['z']) + 40, float(place_point['r']))
            
            print(f"[Task {i+1} completed]")
        
        print("[All tasks completed]")
        
        # Exchange pick and place positions
        pick_points, place_points = place_points, pick_points

if __name__ == "__main__":
    main()
