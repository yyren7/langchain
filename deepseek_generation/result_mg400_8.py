
from dobot_api import DobotApiDashboard, DobotApi, DobotApiMove
import time

def connect_robot():
    dashboard_p = DobotApiDashboard('192.168.250.101', 29999)
    move_p = DobotApiMove('192.168.250.101', 30003)
    feed_p = DobotApi('192.168.250.101', 30004)
    return dashboard_p, move_p, feed_p

def main():
    dashboard_p, move_p, feed_p = connect_robot()
    
    # 启动机器人并等待2秒
    dashboard_p.EnableRobot()
    time.sleep(2)
    
    # 设置机器人速度为最大速度的100%
    dashboard_p.SpeedFactor(100)
    
    pos_object = [[291, 10, 10, 0], [272, 12, 10, 0], [255, 13.5, 10, 0], [237, 14, 10, 0], [290, -178, 10, 0], [271, -177, 10, 0], [252, -177, 10, 0], [233, -177, 10, 0]]
    pos_end = [158, 234, 86, 21]
    DO = 1
    
    k = 0
    while True:
        k += 1
        
        # 1. 先到达抓取开始坐标正上方20cm
        move_p.MovJ(pos_object[k % len(pos_object)][0], pos_object[k % len(pos_object)][1], pos_object[k % len(pos_object)][2] + 20, pos_object[k % len(pos_object)][3])
        move_p.Sync()
        
        # 2. 向正方向下移20cm
        move_p.MovL(pos_object[k % len(pos_object)][0], pos_object[k % len(pos_object)][1], pos_object[k % len(pos_object)][2], pos_object[k % len(pos_object)][3])
        move_p.Sync()
        
        # 3. 启动指定数字输出
        dashboard_p.DO(DO, 1)
        
        # 4. 从当前位置上升20cm
        move_p.MovL(pos_object[k % len(pos_object)][0], pos_object[k % len(pos_object)][1], pos_object[k % len(pos_object)][2] + 20, pos_object[k % len(pos_object)][3])
        move_p.Sync()
        
        # 5. 移动到放置坐标正上方20cm
        move_p.MovJ(pos_end[0], pos_end[1], pos_end[2] + 20, pos_end[3])
        move_p.Sync()
        
        # 6. 向正方向下移20cm
        move_p.MovL(pos_end[0], pos_end[1], pos_end[2], pos_end[3])
        move_p.Sync()
        
        # 7. 关闭指定数字输出
        dashboard_p.DO(DO, 0)
        
        # 8. 从当前位置上升20cm
        move_p.MovL(pos_end[0], pos_end[1], pos_end[2] + 20, pos_end[3])
        move_p.Sync()
        
        print(f"第{k}个任务完成")

if __name__ == "__main__":
    main()
