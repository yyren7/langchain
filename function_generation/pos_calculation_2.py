import numpy as np


def rotate_vector(rotation_angles, vector):
    # 旋转角度
    rx, ry, rz = np.radians(rotation_angles)

    # 旋转矩阵
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
    R = Rz @ Ry @ Rx

    # 旋转向量
    rotated_vector = R @ vector

    return rotated_vector


def move_in_direction(P1, distance):
    # 提取位置和旋转角度
    x, y, z, rx, ry, rz = P1

    # 定义移动向量（负方向）
    move_vector = np.array([0, 0, distance])

    # 旋转移动向量到局部坐标系
    rotated_move_vector = rotate_vector((rx, ry, rz), move_vector)

    # 计算新位置
    new_x = x + rotated_move_vector[0]
    new_y = y + rotated_move_vector[1]
    new_z = z + rotated_move_vector[2]

    # 返回新的六维坐标
    P2 = [new_x, new_y, new_z, rx, ry, rz]
    return P2


if __name__ == '__main__':
    # 示例输入
    P1 = [-175.9049987792968, -691.0740966796875, 487.945343017578, -21.19428062438965, 85.9488525390625,
          -125.2536544799804]  # 单位：mm 和 度
    distance = -100  # 单位：mm

    # 计算移动后的新坐标
    P2 = move_in_direction(P1, distance)

    # 输出结果
    print("移动后的新坐标 P2:", P2)
