import geopandas as gpd
import pandas as pd
import numpy as np
from shapely.geometry import MultiPolygon, Polygon
import warnings
from .config import Config

warnings.filterwarnings('ignore')


class DataProcessor:
    def __init__(self, config=Config):
        self.cfg = config
        self.buildings = None
        self.roads = None
        # 用于存储简化前后的对比样本，供 Visualizer 使用
        self.simplification_samples = {}

    def load_data(self):
        """加载原始数据"""
        print("正在加载数据...")
        try:
            self.buildings = gpd.read_file(self.cfg.BUILDING_PATH)
            self.roads = gpd.read_file(self.cfg.ROAD_PATH)
            print(f"  建筑数据加载成功: {len(self.buildings)} 条")
            print(f"  道路数据加载成功: {len(self.roads)} 条")
        except Exception as e:
            print(f"数据加载失败: {e}")
            raise e

    def _fix_geometry(self, gdf, name="数据"):
        """修复无效几何"""
        invalid_count = (~gdf.geometry.is_valid).sum()
        if invalid_count > 0:
            print(f"  正在修复 {name} 中的 {invalid_count} 个无效几何...")
            gdf.geometry = gdf.geometry.buffer(0)
        return gdf

    def preprocess_roads(self):
        """处理道路数据：筛选类型、投影转换"""
        print("\n处理道路数据...")

        # 1. 坐标系转换
        if self.roads.crs != self.cfg.TARGET_CRS:
            self.roads = self.roads.to_crs(self.cfg.TARGET_CRS)

        # 2. 修复几何
        self.roads = self._fix_geometry(self.roads, "道路")

        # 3. 道路类型筛选
        if self.cfg.ROAD_FILTER_ENABLED:
            col_name = self.cfg.ROAD_TYPE_COLUMN
            if col_name in self.roads.columns:
                initial_count = len(self.roads)
                # 筛选掉在排除列表中的类型
                self.roads = self.roads[~self.roads[col_name].isin(self.cfg.EXCLUDED_ROAD_TYPES)].copy()
                filtered_count = initial_count - len(self.roads)
                print(f"  已根据 '{col_name}' 筛选道路")
                print(f"  - 排除类型: {self.cfg.EXCLUDED_ROAD_TYPES}")
                print(f"  - 移除数量: {filtered_count} ({filtered_count / initial_count * 100:.1f}%)")
                print(f"  - 剩余数量: {len(self.roads)}")
            else:
                print(f"  警告: 未找到道路类型列 '{col_name}'，跳过筛选。")

        return self.roads

    def preprocess_buildings(self):
        """处理建筑数据：采样、投影、计算面积、简化"""
        print("\n处理建筑数据...")

        # 1. 随机采样 (仅在配置了 SAMPLE_SIZE 时执行)
        if self.cfg.SAMPLE_SIZE and self.cfg.SAMPLE_SIZE < len(self.buildings):
            print(f"  执行随机采样: {self.cfg.SAMPLE_SIZE}")
            self.buildings = self.buildings.sample(n=self.cfg.SAMPLE_SIZE, random_state=self.cfg.RANDOM_SEED).copy()

        # 2. 坐标系转换
        if self.buildings.crs != self.cfg.TARGET_CRS:
            self.buildings = self.buildings.to_crs(self.cfg.TARGET_CRS)

        # 3. 修复几何
        self.buildings = self._fix_geometry(self.buildings, "建筑")

        # 4. 确保有 Building ID
        if 'building_id' not in self.buildings.columns:
            self.buildings['building_id'] = range(1, len(self.buildings) + 1)

        # 5. 计算面积并过滤
        self.buildings['area_sqm'] = self.buildings.geometry.area
        count_before = len(self.buildings)
        self.buildings = self.buildings[self.buildings['area_sqm'] >= self.cfg.MIN_BUILDING_AREA].copy()
        print(f"  过滤小面积建筑 (<{self.cfg.MIN_BUILDING_AREA}m²): 移除 {count_before - len(self.buildings)} 个")

        # ==========================================
        # 保存简化前的样本用于可视化对比
        # ==========================================
        # 随机选 3 个建筑 ID (或者更少，如果建筑总数不足3个)
        n_samples = min(3, len(self.buildings))
        if n_samples > 0:
            sample_ids = self.buildings.sample(n=n_samples, random_state=self.cfg.RANDOM_SEED)['building_id'].values
            # 保存原始几何的副本
            self.simplification_samples['original'] = self.buildings[
                self.buildings['building_id'].isin(sample_ids)].copy()
        else:
            sample_ids = []

        # 6. 几何简化
        print(f"  执行轮廓简化 (Tolerance={self.cfg.SIMPLIFY_TOLERANCE})...")
        self.buildings.geometry = self.buildings.geometry.simplify(
            tolerance=self.cfg.SIMPLIFY_TOLERANCE,
            preserve_topology=True
        )

        # ==========================================
        # 保存简化后的样本
        # ==========================================
        if len(sample_ids) > 0:
            self.simplification_samples['simplified'] = self.buildings[
                self.buildings['building_id'].isin(sample_ids)].copy()

        # 重置索引
        self.buildings = self.buildings.reset_index(drop=True)
        return self.buildings

    def run(self):
        """执行完整的数据处理流程"""
        self.load_data()
        self.preprocess_roads()
        self.preprocess_buildings()
        print("\n数据预处理完成")
        return self.buildings, self.roads