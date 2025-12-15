import geopandas as gpd
import pandas as pd
from shapely.geometry import GeometryCollection, MultiLineString
from shapely.ops import nearest_points
from tqdm import tqdm
from .config import cfg
from .utils import calculate_midpoints, calculate_heading_angle

class StreetViewSampler:
    """核心业务逻辑类：生成街景采样点"""
    
    def __init__(self, buildings_gdf, roads_gdf):
        self.buildings = buildings_gdf
        self.roads = roads_gdf
        self.results = []
        
    def simplify_buildings(self):
        """简化建筑轮廓"""
        print(f"\n 正在简化建筑轮廓 (Tolerance={cfg.SIMPLIFY_TOLERANCE}m)...")
        self.buildings['geometry_simplified'] = self.buildings.geometry.simplify(
            tolerance=cfg.SIMPLIFY_TOLERANCE, 
            preserve_topology=True
        )
        
    def generate_points(self):
        """执行核心采样算法"""
        if 'geometry_simplified' not in self.buildings.columns:
            self.simplify_buildings()
            
        print("\n 开始生成采样点...")
        
        # 预先计算所有中点 (这里简化逻辑，在循环中处理或优化为空间索引)
        # 为演示清晰，采用逐个建筑处理的逻辑
        
        for idx, row in tqdm(self.buildings.iterrows(), total=len(self.buildings), desc="Processing"):
            self._process_single_building(idx, row)
            
        return pd.DataFrame(self.results)
    
    def _process_single_building(self, idx, row):
        """处理单个建筑"""
        building_id = row['building_id']
        geom = row['geometry_simplified']
        
        # 1. 缓冲区裁剪道路
        buffer = geom.buffer(cfg.BUFFER_DISTANCE)
        possible_roads = self.roads[self.roads.intersects(buffer)]
        
        if possible_roads.empty:
            return
            
        # 合并道路几何
        road_union = possible_roads.geometry.unary_union
        
        # 2. 计算该建筑的所有边中点
        midpoints = calculate_midpoints(geom)
        
        # 3. 寻找最佳采样点
        best_match = self._find_best_viewpoint(midpoints, road_union)
        
        if best_match:
            best_match.update({
                'building_id': building_id,
                'building_area': row['area_sqm']
            })
            self.results.append(best_match)
            
    def _find_best_viewpoint(self, midpoints, road_geom):
        """在候选道路上寻找离建筑边中点最近的点"""
        shortest_dist = float('inf')
        best_data = None
        
        for mp_info in midpoints:
            mp_geom = mp_info['midpoint']
            
            # 找到道路上最近的点
            nearest_road_point = nearest_points(mp_geom, road_geom)[1]
            dist = mp_geom.distance(nearest_road_point)
            
            if dist < shortest_dist and dist <= cfg.MAX_DISTANCE:
                shortest_dist = dist
                
                # 计算 Heading
                heading = calculate_heading_angle(
                    nearest_road_point.x, nearest_road_point.y,
                    mp_geom.x, mp_geom.y
                )
                
                best_data = {
                    'sample_point_x': nearest_road_point.x,
                    'sample_point_y': nearest_road_point.y,
                    'building_center_x': mp_geom.x,
                    'building_center_y': mp_geom.y,
                    'edge_index': mp_info['edge_index'],
                    'distance': round(dist, 2),
                    'heading': heading,
                    'confidence': max(0, 100 - dist)
                }
                
        return best_data
