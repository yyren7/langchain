
from dobot_api import DobotApiDashboard, DobotApi, DobotApiMove
import time

def connect_robot():
    ip = "192.168.250.101"
    dashboard_p = DobotApiDashboard(ip, 29999)
    move_p = DobotApiMove(ip, 30003)
    feed_p = DobotApi(ip, 30004)
    return dashboard_p, move_p, feed_p

def calculate_new_position(pos, offset):
    # 计算新的抓取和放置坐标
    new_pos = [pos[0] + offset[0], pos[1] + offset[1], pos[2] + offset[2], pos[3] + offset[3]]
    return new_pos

def move_to_position(move_p, pos):
    # 移动到指定位置
    move_p.MovJ(pos[0], pos[1], pos[2], pos[3])

def jog_up_and_back(move_p, pos):
    # 以工具坐标为基准向上移动10cm再后退回来
    move_p.Jog(0, 0, 10, 0)  # 向上移动10cm
    time.sleep(1)
    move_p.Jog(0, 0, -10, 0)  # 后退回来
    time.sleep(1)

def main():
    dashboard_p, move_p, feed_p = connect_robot()

    # 启动机器人
    dashboard_p.EnableRobot()
    time.sleep(2)

    pos_start = [284, 4, 90, -43]
    pos_end = [280, 104, 80, -23]
    offset = [0, 0, -10, 0]  # 以当前工具朝向为基准向反方向移动10厘米

    while True:
        # 计算新的抓取和放置坐标
        new_pos_start = calculate_new_position(pos_start, offset)
        new_pos_end = calculate_new_position(pos_end, offset)

        # 移动到新的抓取位置
        move_to_position(move_p, new_pos_start)
        time.sleep(2)

        # 抓取动作：向上移动10cm再后退回来
        jog_up_and_back(move_p, new_pos_start)

        # 移动到新的放置位置
        move_to_position(move_p, new_pos_end)
        time.sleep(2)

        # 放置动作：向上移动10cm再后退回来
        jog_up_and_back(move_p, new_pos_end)

        # 返回字符串“ok”
        print("ok")

    # 关闭机器人
    dashboard_p.DisableRobot()

if __name__ == "__main__":
    main()
