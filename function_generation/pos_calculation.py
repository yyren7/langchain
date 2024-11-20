import numpy as np


def rotation_matrix_from_euler(rx, ry, rz):
    # 将角度转换为弧度
    rx = np.radians(rx)
    ry = np.radians(ry)
    rz = np.radians(rz)

    # 构建旋转矩阵
    Rx = np.array([[1, 0, 0],
                   [0, np.cos(rx), -np.sin(rx)],
                   [0, np.sin(rx), np.cos(rx)]])

    Ry = np.array([[np.cos(ry), 0, np.sin(ry)],
                   [0, 1, 0],
                   [-np.sin(ry), 0, np.cos(ry)]])

    Rz = np.array([[np.cos(rz), -np.sin(rz), 0],
                   [np.sin(rz), np.cos(rz), 0],
                   [0, 0, 1]])

    # 组合旋转矩阵
    R = np.dot(Rz, np.dot(Ry, Rx))
    return R


def move_forward(xyz, rxryrz, distance):
    # 提取旋转角度
    rx, ry, rz = rxryrz

    # 获取旋转矩阵
    R = rotation_matrix_from_euler(rx, ry, rz)

    # 负方向的单位向量
    forward_vector = np.array([0, 0, -1])

    # 应用旋转矩阵
    rotated_forward_vector = np.dot(R, forward_vector)

    # 计算移动后的新坐标
    new_xyz = xyz + rotated_forward_vector * distance

    return new_xyz


# 示例使用
P1=[-175.9049987792968, -691.0740966796875, 487.945343017578, -21.19428062438965, 85.9488525390625, -125.2536544799804]
xyz = np.array([-175.9049987792968, -691.0740966796875,487.945343017578])  # 当前位置
rxryrz = (-21.19428062438965, 85.9488525390625, -125.2536544799804)  # 旋转角度（绕X轴、Y轴、Z轴）

distance = 100.0  # 移动距离（10cm）

new_xyz = move_forward(xyz, rxryrz, distance)
print("New coordinates:", new_xyz[0],",",new_xyz[1],",",new_xyz[2])
P2=[-168.65752054537558 , -662.0298325583323 , 485.96929117165035, -21.19428062438965, 85.9488525390625, -125.2536544799804]
# New coordinates: [-173.4891727,-681.39267531,487.28665907]