
import json
import time
from dobot_api import DobotApiDashboard, DobotApi, DobotApiMove

def connect_robot():
    ip = "192.168.250.101"
    dashboard_port = 29999
    move_port = 30003
    feed_port = 30004
    
    dashboard_client = DobotApiDashboard(ip, dashboard_port)
    move_client = DobotApiMove(ip, move_port)
    feed_client = DobotApi(ip, feed_port)
    
    return dashboard_client, move_client, feed_client

def load_points(file_path):
    with open(file_path, 'r') as file:
        data = json.load(file)
    return data['groups']

def move_to_position(move_client, x, y, z, r):
    move_client.MovJ(x, y, z, r)
    move_client.Sync()

def activate_digital_output(dashboard_client, do_index):
    dashboard_client.DO(do_index, 1)
    time.sleep(0.2)  # Wait for 0.2 second after turning off the digital output
def deactivate_digital_output(dashboard_client, do_index):
    dashboard_client.DO(do_index, 0)
    time.sleep(0.2)  # Wait for 0.2 second after turning off the digital output

def main():
    dashboard_client, move_client, feed_client = connect_robot()
    
    # Activate the robot
    dashboard_client.EnableRobot()
    time.sleep(2)
    
    # Set speed to 50%
    dashboard_client.SpeedFactor(50)
    
    points = load_points('./generated_points.json')
    pick_points = points[0]['coordinates']
    place_points = points[1]['coordinates']
    
    do_index = 1  # Digital output index
    
    while True:
        for k in range(len(pick_points)):
            pick_point = pick_points[k]
            place_point = place_points[k]
            
            # Move 40 cm above the pick point
            move_to_position(move_client, float(pick_point['x']), float(pick_point['y']), float(pick_point['z']) + 40, float(pick_point['r']))
            
            # Move down 40 cm
            move_to_position(move_client, float(pick_point['x']), float(pick_point['y']), float(pick_point['z']), float(pick_point['r']))
            
            # Activate digital output
            activate_digital_output(dashboard_client, do_index)
            
            # Ascend 40 cm
            move_to_position(move_client, float(pick_point['x']), float(pick_point['y']), float(pick_point['z']) + 40, float(pick_point['r']))
            
            # Move 40 cm above the place point
            move_to_position(move_client, float(place_point['x']), float(place_point['y']), float(place_point['z']) + 40, float(place_point['r']))
            
            # Move down 40 cm
            move_to_position(move_client, float(place_point['x']), float(place_point['y']), float(place_point['z']), float(place_point['r']))
            
            # Deactivate digital output
            deactivate_digital_output(dashboard_client, do_index)
            
            # Ascend 40 cm
            move_to_position(move_client, float(place_point['x']), float(place_point['y']), float(place_point['z']) + 40, float(place_point['r']))
            
            print(f"[Task {k+1} completed]")
        
        print("[All tasks completed]")
        
        # Exchange pick and place positions
        pick_points, place_points = place_points, pick_points

if __name__ == "__main__":
    main()
