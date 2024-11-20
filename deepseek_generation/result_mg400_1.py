
import time
import dobot

# 机器人IP地址
ip = "192.168.250.101"

# 起始和结束位置
pos_start = [284, 4, 90, -43]
pos_end = [280, 104, 80, -23]

# 计算新的抓取和放置位置（反方向移动10cm）
def calculate_new_position(pos, offset):
    # 假设工具朝向为Z轴方向
    new_pos = [pos[0], pos[1], pos[2] - offset, pos[3]]
    return new_pos

# 初始化机器人
robot = dobot.Dobot(ip)
robot.connect()
time.sleep(2)  # 等待机器人启动

try:
    while True:
        # 计算新的抓取位置
        new_pos_start = calculate_new_position(pos_start, 10)
        
        # 移动到新的抓取位置
        robot.move_to(new_pos_start)
        
        # 使用jog命令前移10cm再后退
        robot.jog(10, 'z')  # 前移10cm
        robot.jog(-10, 'z')  # 后退10cm
        
        # 计算新的放置位置
        new_pos_end = calculate_new_position(pos_end, 10)
        
        # 移动到新的放置位置
        robot.move_to(new_pos_end)
        
        # 使用jog命令前移10cm再后退
        robot.jog(10, 'z')  # 前移10cm
        robot.jog(-10, 'z')  # 后退10cm
        
except KeyboardInterrupt:
    pass

finally:
    # 关闭机器人
    robot.disconnect()
