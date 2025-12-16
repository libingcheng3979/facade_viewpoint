import geopandas as gpd
import pandas as pd
import numpy as np
from tqdm import tqdm
from shapely.ops import nearest_points
from shapely.geometry import MultiLineString, GeometryCollection
from .config import Config
from .geometry_utils import calculate_polygon_edge_midpoints, calculate_heading


class Sampler:
    def __init__(self, config=Config):
        self.cfg = config

    def generate_building_midpoints(self, buildings_gdf):
        """
        Step 4: 为所有建筑生成边中点
        """
        print("\n计算建筑各边中点...")
        all_midpoints = []

        # 使用 itertuples 通常比 iterrows 快
        # 但为了保持逻辑简单，且需要 geometry，这里用 iterrows 配合 tqdm
        for idx, row in tqdm(buildings_gdf.iterrows(), total=len(buildings_gdf), desc="  提取中点"):
            midpoints = calculate_polygon_edge_midpoints(row.geometry)

            # 附加元数据
            for mp in midpoints:
                mp['building_id'] = row['building_id']
                mp['building_area'] = row['area_sqm']  # 顺便带上面积，后续用
                # mp['building_idx'] = idx # 不需要原始索引，用ID即可

            all_midpoints.extend(midpoints)

        # 转换为 GeoDataFrame
        midpoints_gdf = gpd.GeoDataFrame(
            all_midpoints,
            geometry='midpoint',
            crs=buildings_gdf.crs
        )
        print(f"共生成 {len(midpoints_gdf)} 个边中点")
        return midpoints_gdf

    def execute_sampling(self, buildings_gdf, roads_gdf, midpoints_gdf):
        """
        Step 5: 核心采样循环
        """
        print("\n开始匹配最近道路采样点...")

        results = []
        stats = {'with_roads': 0, 'no_roads': 0, 'too_far': 0}

        # 建立空间索引 (虽然 intersects 会自动用，但显式调用是个好习惯)
        sindex = roads_gdf.sindex

        # 主循环：遍历每个建筑
        for idx, building in tqdm(buildings_gdf.iterrows(), total=len(buildings_gdf), desc="  采样进度"):
            res = self._process_single_building(building, roads_gdf, midpoints_gdf)

            if res:
                results.append(res)
                stats['with_roads'] += 1
            else:
                # 简单统计失败原因（这里简化处理，通常是因为缓冲区没路或距离太远）
                stats['no_roads'] += 1

        # 创建结果 DataFrame
        results_df = pd.DataFrame(results)

        print(f"采样完成")
        print(f"  - 成功采样: {len(results_df)} ({len(results_df) / len(buildings_gdf) * 100:.1f}%)")
        print(f"  - 未找到合适点: {len(buildings_gdf) - len(results_df)}")

        return results_df

    def _process_single_building(self, building, roads_gdf, all_midpoints_gdf):
        """处理单个建筑的采样逻辑"""

        # 1. 获取该建筑的所有中点
        # 优化：这里每次查询全量 midpoints_gdf 可能较慢
        # 但由于 midpoints_gdf 已经是构建好的，用 pandas 筛选尚可
        # 极致优化是将 midpoints 按 building_id 分组存储在 dict 中，但先保持原逻辑
        b_midpoints = all_midpoints_gdf[all_midpoints_gdf['building_id'] == building['building_id']]

        if len(b_midpoints) == 0:
            return None

        # 2. 空间查询：找到缓冲区内的道路
        buffer = building.geometry.buffer(self.cfg.BUFFER_DISTANCE)
        possible_roads_idx = list(roads_gdf.sindex.query(buffer, predicate='intersects'))

        if not possible_roads_idx:
            return None

        nearby_roads = roads_gdf.iloc[possible_roads_idx]
        # 精确裁剪 (intersect)
        road_clip = nearby_roads[nearby_roads.intersects(buffer)]

        if road_clip.empty:
            return None

        # 3. 合并道路几何以进行最近点计算
        # unary_union 有时比 GeometryCollection 鲁棒，但这里 Collection 够快
        road_geoms = road_clip.geometry.values
        if len(road_geoms) == 1:
            road_union = road_geoms[0]
        else:
            road_union = GeometryCollection(list(road_geoms))

        # 4. 遍历该建筑所有边中点，找全局最近点
        best_sample = None
        min_dist = float('inf')

        for _, mp_row in b_midpoints.iterrows():
            mp_geom = mp_row['midpoint']

            # 找道路上最近的点
            # nearest_points 返回 (geom1_nearest, geom2_nearest)
            try:
                p_road = nearest_points(mp_geom, road_union)[1]
                dist = mp_geom.distance(p_road)

                if dist < min_dist:
                    min_dist = dist
                    best_sample = {
                        'sample_point': p_road,
                        'building_midpoint': mp_geom,
                        'edge_index': mp_row['edge_index'],
                        'dist': dist
                    }
            except Exception:
                continue

        # 5. 最终校验
        if best_sample and best_sample['dist'] <= self.cfg.MAX_DISTANCE:
            # 计算 Heading
            sp = best_sample['sample_point']
            bp = best_sample['building_midpoint']
            heading = calculate_heading(sp.x, sp.y, bp.x, bp.y)

            # 计算置信度
            confidence = max(0, 100 - best_sample['dist'])

            return {
                'building_id': building['building_id'],
                'lat': sp.y,  # 注意：这里还是投影坐标，后续统一转经纬度
                'lng': sp.x,
                'heading': heading,
                'distance': round(best_sample['dist'], 2),
                'confidence': round(confidence, 2),
                'edge_index': best_sample['edge_index'],
                'building_area': building['area_sqm'],
                # 保存几何对象用于后续转换
                'geometry_sample': sp,
                'geometry_midpoint': bp
            }

        return None