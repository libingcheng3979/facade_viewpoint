import geopandas as gpd
import pandas as pd
from .config import cfg

def load_and_preprocess_data():
    """加载、清洗并预处理建筑和道路数据"""
    
    # 1. 加载数据
    print(f"\n 正在加载数据...")
    if not cfg.BUILDING_PATH.exists() or not cfg.ROAD_PATH.exists():
        raise FileNotFoundError(f"输入文件不存在，请检查 data/input 目录。\n期望路径:\n{cfg.BUILDING_PATH}\n{cfg.ROAD_PATH}")

    buildings = gpd.read_file(cfg.BUILDING_PATH)
    roads = gpd.read_file(cfg.ROAD_PATH)
    
    print(f"✓ 加载完成: 建筑 {len(buildings)} 个, 道路 {len(roads)} 条")

    # 2. 道路筛选
    if cfg.ENABLE_ROAD_FILTERING and cfg.ROAD_TYPE_FIELD in roads.columns:
        print(f" 执行道路类型筛选...")
        initial_count = len(roads)
        roads = roads[~roads[cfg.ROAD_TYPE_FIELD].isin(cfg.EXCLUDED_ROAD_TYPES)].copy()
        print(f"  - 排除: {initial_count - len(roads)} 条不适合的道路")
    
    # 3. 几何修复
    buildings.geometry = buildings.geometry.buffer(0)
    roads.geometry = roads.geometry.buffer(0)
    
    # 4. 坐标转换
    print(f" 转换坐标系至 {cfg.TARGET_CRS}...")
    buildings_proj = buildings.to_crs(cfg.TARGET_CRS)
    roads_proj = roads.to_crs(cfg.TARGET_CRS)
    
    # 5. 建筑面积过滤
    buildings_proj['area_sqm'] = buildings_proj.geometry.area
    buildings_filtered = buildings_proj[buildings_proj['area_sqm'] >= cfg.MIN_BUILDING_AREA].copy()
    
    # 6. 随机采样
    if cfg.SAMPLE_SIZE and cfg.SAMPLE_SIZE < len(buildings_filtered):
        print(f" 随机采样 {cfg.SAMPLE_SIZE} 个建筑...")
        buildings_final = buildings_filtered.sample(n=cfg.SAMPLE_SIZE, random_state=cfg.RANDOM_SEED).copy()
    else:
        buildings_final = buildings_filtered
        
    # 添加ID
    if 'building_id' not in buildings_final.columns:
        buildings_final['building_id'] = range(1, len(buildings_final) + 1)
        
    return buildings_final.reset_index(drop=True), roads_proj
