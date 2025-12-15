import os
from pathlib import Path

class Config:
    """配置参数类 - 集中管理所有可调参数"""
    
    # 获取项目根目录 (假设 config.py 在 src/ 目录下，向上两级是根目录)
    PROJECT_ROOT = Path(__file__).parent.parent
    
    # -------------------- 输入文件路径 --------------------
    # 建议将数据放入 data/input 目录，这里使用相对路径
    DATA_DIR = PROJECT_ROOT / "data"
    INPUT_DIR = DATA_DIR / "input"
    OUTPUT_DIR = DATA_DIR / "output"
    
    # TODO: 请用户根据实际文件名修改这里
    BUILDING_FILENAME = "Building_Footprints_20251214.geojson"
    ROAD_FILENAME = "roads_sfc.geojson"
    
    @property
    def BUILDING_PATH(self):
        return self.INPUT_DIR / self.BUILDING_FILENAME

    @property
    def ROAD_PATH(self):
        return self.INPUT_DIR / self.ROAD_FILENAME
    
    # -------------------- 采样参数 --------------------
    SAMPLE_SIZE = 500          # 随机采样建筑数量（None表示处理全部）
    RANDOM_SEED = 42            # 随机种子
    
    # -------------------- 处理参数 --------------------
    SIMPLIFY_TOLERANCE = 2      # 建筑简化容差（米）
    BUFFER_DISTANCE = 50        # 建筑缓冲区距离（米）
    MAX_DISTANCE = 100          # 最大采样点距离阈值（米）
    MIN_BUILDING_AREA = 20      # 最小建筑面积阈值（平方米）
    
    # -------------------- 道路筛选参数 --------------------
    ENABLE_ROAD_FILTERING = False
    ROAD_TYPE_FIELD = 'type'
    EXCLUDED_ROAD_TYPES = [
        'motorway', 'motorway_link', 'trunk', 'trunk_link',
        'steps', 'cycleway', 'footway', 'path', 'pedestrian',
        'service', 'construction'
    ]
    
    # -------------------- 坐标系参数 --------------------
    TARGET_CRS = "EPSG:32610"   # UTM Zone 10N (投影坐标系，用于计算距离)
    OUTPUT_CRS = "EPSG:4326"    # WGS84 (经纬度，用于输出结果)
    
    # -------------------- 输出配置 --------------------
    OUTPUT_CSV_NAME = "building_streetview_samples.csv"
    
    # 确保输出目录存在
    def __init__(self):
        os.makedirs(self.OUTPUT_DIR, exist_ok=True)
        print(f"配置已加载。根目录: {self.PROJECT_ROOT}")

# 实例化供其他模块调用
cfg = Config()
