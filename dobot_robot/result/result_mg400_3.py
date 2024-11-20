
from dobot_api import DobotApiDashboard, DobotApi, DobotApiMove
import time

def connect_robot():
    ip = "192.168.250.101"
    dashboard_p = DobotApiDashboard(ip, 29999)
    move_p = DobotApiMove(ip, 30003)
    feed_p = DobotApi(ip, 30004)
    return dashboard_p, move_p, feed_p

def move_to_position(move_p, position):
    move_p.MovJ(position[0], position[1], position[2], position[3])

def main():
    dashboard_p, move_p, feed_p = connect_robot()
    
    # 启动机器人
    dashboard_p.EnableRobot()
    time.sleep(2)

    pos_start = [284, 4, 90, -43]
    pos_end = [280, 104, 80, -23]
    DO = 1

    while True:
        # 移动到抓取开始位置（实际抓取位置上方10cm）
        move_to_position(move_p, [pos_start[0], pos_start[1], pos_start[2] + 10, pos_start[3]])
        
        # 向下移动10cm并启动数字输出
        move_to_position(move_p, pos_start)
        dashboard_p.DO(DO, 1)
        
        # 后退
        move_to_position(move_p, [pos_start[0], pos_start[1], pos_start[2] + 10, pos_start[3]])
        
        # 移动到放置位置
        move_to_position(move_p, pos_end)
        
        # 关闭数字输出
        dashboard_p.DO(DO, 0)
        
        # 返回字符串“任务完成”
        print("任务完成")

    # 关闭机器人
    dashboard_p.DisableRobot()

if __name__ == "__main__":
    main()
