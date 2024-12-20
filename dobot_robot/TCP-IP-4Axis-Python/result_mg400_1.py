
from dobot_api import DobotApiDashboard, DobotApi, DobotApiMove
import time

def connect_robot():
    dashboard_p = DobotApiDashboard('192.168.250.101', 29999)
    move_p = DobotApiMove('192.168.250.101', 30003)
    return dashboard_p, move_p

def calculate_new_position(pos, offset):
    # 计算新的抓取和放置坐标
    new_pos = pos[:]
    new_pos[0] -= offset
    return new_pos

def move_to_position(move_p, pos):
    # 移动到指定位置
    move_p.MovL(pos[0], pos[1], pos[2], pos[3])
    time.sleep(2)  # 等待机器人到达目标位置

def jog_forward_backward(move_p, pos, offset):
    # 前移10cm再后退回来
    move_p.MovL(pos[0] , pos[1], pos[2]+ offset, pos[3])
    time.sleep(2)
    move_p.MovL(pos[0], pos[1], pos[2], pos[3])
    time.sleep(2)

def main():
    dashboard_p, move_p = connect_robot()
    
    # 启动机器人
    dashboard_p.EnableRobot()
    time.sleep(2)
    
    pos_start = [284, 4, 90, -43]
    pos_end = [280, 104, 80, -23]
    offset = 10  # 10 cm
    
    while True:
        # 计算新的抓取和放置坐标
        new_pos_start = calculate_new_position(pos_start, offset)
        new_pos_end = calculate_new_position(pos_end, offset)
        
        # 移动到新的抓取位置
        move_to_position(move_p, new_pos_start)
        
        # 前移10cm再后退回来
        jog_forward_backward(move_p, new_pos_start, offset)
        
        # 移动到新的放置位置
        move_to_position(move_p, new_pos_end)
        
        # 前移10cm再后退回来
        jog_forward_backward(move_p, new_pos_end, offset)
        
        # 返回字符串“ok”
        print("ok")

    # 关闭机器人
    dashboard_p.DisableRobot()
    dashboard_p.close()
    move_p.close()

if __name__ == "__main__":
    main()
