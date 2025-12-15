import numpy as np
from shapely.geometry import Point, Polygon, MultiPolygon

def count_vertices(geom):
    """计算几何对象的顶点总数"""
    if isinstance(geom, Polygon):
        return len(geom.exterior.coords)
    elif isinstance(geom, MultiPolygon):
        return sum(len(poly.exterior.coords) for poly in geom.geoms)
    return 0

def calculate_midpoints(geometry):
    """
    计算建筑物各边的中点
    返回: list of dict: [{'edge_index': int, 'midpoint': Point}, ...]
    """
    midpoints = []
    edge_index = 0
    
    if isinstance(geometry, MultiPolygon):
        polygons = list(geometry.geoms)
    else:
        polygons = [geometry]
    
    for polygon in polygons:
        coords = list(polygon.exterior.coords)
        for i in range(len(coords) - 1):
            point1 = coords[i]
            point2 = coords[i + 1]
            
            mid_x = (point1[0] + point2[0]) / 2.0
            mid_y = (point1[1] + point2[1]) / 2.0
            midpoint = Point(mid_x, mid_y)
            
            midpoints.append({
                'edge_index': edge_index,
                'midpoint': midpoint
            })
            edge_index += 1
            
    return midpoints

def calculate_heading_angle(xs, ys, xc, yc):
    """
    计算从采样点(xs, ys)指向建筑中点(xc, yc)的角度（0-360度，正北为0）
    """
    # 定义正北方向向量 Vn
    Vn = np.array([xs, ys + 1]) - np.array([xs, ys])
    # 定义从采样点指向建筑中点的向量 Vsc
    Vsc = np.array([xc - xs, yc - ys])
    
    dot_product = np.dot(Vn, Vsc)
    norm_Vn = np.linalg.norm(Vn)
    norm_Vsc = np.linalg.norm(Vsc)
    
    if norm_Vsc == 0: return 0 # 避免除零
    
    cos_theta = dot_product / (norm_Vn * norm_Vsc)
    cos_theta = np.clip(cos_theta, -1.0, 1.0)
    
    if (xc - xs) > 0:
        theta = np.degrees(np.arccos(cos_theta))
    else:
        theta = 360 - np.degrees(np.arccos(cos_theta))
        
    return round(theta, 2)
