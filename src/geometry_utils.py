import numpy as np
from shapely.geometry import Point, MultiPolygon, Polygon


def calculate_polygon_edge_midpoints(geometry, start_edge_index=0):
    """
    计算多边形各边的中点

    Args:
        geometry: Shapely Polygon or MultiPolygon
        start_edge_index: 起始的边索引编号

    Returns:
        list of dict: [{'edge_index': int, 'midpoint': Point}, ...]
    """
    midpoints = []
    current_edge_idx = start_edge_index

    # 统一转为列表处理，兼容 Polygon 和 MultiPolygon
    if isinstance(geometry, MultiPolygon):
        polys = list(geometry.geoms)
    else:
        polys = [geometry]

    for poly in polys:
        # 获取外环坐标
        coords = list(poly.exterior.coords)
        # 遍历每一条边 (点i -> 点i+1)
        for i in range(len(coords) - 1):
            p1 = coords[i]
            p2 = coords[i + 1]

            # 计算中点坐标
            mid_x = (p1[0] + p2[0]) / 2.0
            mid_y = (p1[1] + p2[1]) / 2.0

            midpoints.append({
                'edge_index': current_edge_idx,
                'midpoint': Point(mid_x, mid_y)
            })
            current_edge_idx += 1

    return midpoints


def calculate_heading(xs, ys, xc, yc):
    """
    计算从采样点(xs, ys)指向建筑点(xc, yc)的角度（0度为正北）

    Args:
        xs, ys: 道路采样点坐标 (Source)
        xc, yc: 建筑目标点坐标 (Target)

    Returns:
        float: 角度 (0-360)
    """
    # 1. 定义正北方向向量 Vn (0, 1)
    # 这里不需要归一化，因为长度为1
    Vn = np.array([0, 1])

    # 2. 定义从采样点指向建筑的向量 Vsc
    Vsc = np.array([xc - xs, yc - ys])

    # 3. 计算模长
    norm_Vsc = np.linalg.norm(Vsc)
    if norm_Vsc == 0:
        return 0.0

    # 4. 计算点积和夹角余弦
    # dot(A, B) = |A|*|B|*cos(theta) -> cos(theta) = dot / (|A|*|B|)
    # 因为 |Vn|=1，所以分母主要是 norm_Vsc
    dot_product = np.dot(Vn, Vsc)
    cos_theta = dot_product / norm_Vsc

    # 防止浮点数误差导致超出 [-1, 1]
    cos_theta = np.clip(cos_theta, -1.0, 1.0)

    # 5. 计算角度 (arccos 得到的是 0-180 度)
    theta = np.degrees(np.arccos(cos_theta))

    # 6. 判断方向（左还是右），决定是 0-180 还是 180-360
    # 利用向量叉乘或者简单的 x 坐标判断
    # 如果建筑在采样点的右侧 (dx > 0)，角度即为 theta
    # 如果建筑在采样点的左侧 (dx < 0)，角度为 360 - theta
    if (xc - xs) >= 0:
        final_heading = theta
    else:
        final_heading = 360 - theta

    return round(final_heading, 2)