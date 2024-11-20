
from dobot_api import DobotApiDashboard, DobotApi, DobotApiMove
import time

def connect_robot():
    dashboard_p = DobotApiDashboard('192.168.250.101', 29999)
    move_p = DobotApiMove('192.168.250.101', 30003)
    feed_p = DobotApi('192.168.250.101', 30004)
    return dashboard_p, move_p, feed_p

def move_to_position(move_p, position):
    move_p.MovJ(position[0], position[1], position[2], position[3])

def main():
    dashboard_p, move_p, feed_p = connect_robot()
    
    # 启动机器人
    dashboard_p.EnableRobot()
    time.sleep(2)

    pos_start = [284, 4, 0, -43]
    pos_end = [158, 234, 86, 21]
    DO = 1

    for _ in range(10):
        # 计算抓取的开始坐标（实际抓取坐标的上方20cm）
        pick_start = pos_start.copy()
        pick_start[2] += 20

        # 先到达抓取开始坐标
        move_to_position(move_p, pick_start)
        time.sleep(1)

        # 向正方向下移10cm
        pick_start[2] -= 10
        move_to_position(move_p, pick_start)
        time.sleep(1)

        # 启动指定数字输出
        dashboard_p.DO(DO, 1)
        time.sleep(1)

        # 再上升20cm
        pick_start[2] += 20
        move_to_position(move_p, pick_start)
        time.sleep(1)

        # 移动到放置坐标
        move_to_position(move_p, pos_end)
        time.sleep(1)

        # 关闭指定数字输出
        dashboard_p.DO(DO, 0)
        time.sleep(1)

    # 关闭机器人
    dashboard_p.DisableRobot()

    return "任务完成"

if __name__ == "__main__":
    result = main()
    print(result)
