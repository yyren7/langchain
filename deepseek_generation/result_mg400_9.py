
from dobot_api import DobotApiDashboard, DobotApi, DobotApiMove
import time

def connect_robot():
    dashboard_client = DobotApiDashboard("192.168.250.101", 29999)
    move_client = DobotApiMove("192.168.250.101", 30003)
    feed_client = DobotApi("192.168.250.101", 30004)
    return dashboard_client, move_client, feed_client

def main():
    dashboard_client, move_client, feed_client = connect_robot()
    
    # 启动机器人并等待2秒
    dashboard_client.EnableRobot()
    time.sleep(2)
    
    # 设置速度为最大速度的100%
    dashboard_client.SpeedFactor(100)
    
    pos_object = [[291, 10, 12, 0], [272, 12, 12, 0], [255, 13.5, 12, 0], [237, 14, 12, 0], [290, -178, 12, 0], [271, -177, 12, 0], [252, -177, 12, 0], [233, -177, 12, 0]]
    pos_end = [158, 234, 36, 21]
    DO = 1
    
    k = 0
    while True:
        if k >= len(pos_object):
            k = 0
            print("任务完成")
        
        # 1. 到达抓取开始坐标正上方20cm
        move_client.MovJ(pos_object[k][0], pos_object[k][1], pos_object[k][2] + 20, pos_object[k][3])
        move_client.Sync()
        
        # 2. 向正方向下移20cm
        move_client.MovL(pos_object[k][0], pos_object[k][1], pos_object[k][2], pos_object[k][3])
        move_client.Sync()
        
        # 3. 启动指定数字输出
        dashboard_client.DO(DO, 1)
        
        # 4. 从当前位置上升20cm
        move_client.MovL(pos_object[k][0], pos_object[k][1], pos_object[k][2] + 20, pos_object[k][3])
        move_client.Sync()
        
        # 5. 移动到放置坐标正上方20cm
        move_client.MovJ(pos_end[0], pos_end[1], pos_end[2] + 20, pos_end[3])
        move_client.Sync()
        
        # 6. 向正方向下移20cm
        move_client.MovL(pos_end[0], pos_end[1], pos_end[2], pos_end[3])
        move_client.Sync()
        
        # 7. 关闭指定数字输出
        dashboard_client.DO(DO, 0)
        
        # 8. 从当前位置上升20cm
        move_client.MovL(pos_end[0], pos_end[1], pos_end[2] + 20, pos_end[3])
        move_client.Sync()
        
        print(f"第{k+1}个任务完成")
        k += 1

if __name__ == "__main__":
    main()
