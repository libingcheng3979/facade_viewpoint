import os


class Config:
    # ==========================
    # 路径配置
    # ==========================
    # 建议使用相对路径或在实例化时传入，这里作为默认值
    BUILDING_PATH = "./data/input/Building_Footprints_20251214.geojson"
    ROAD_PATH = "./data/input/roads_sfc.geojson"

    # ==========================
    # 坐标系参数
    # ==========================
    TARGET_CRS = "EPSG:32610"  # 投影坐标系（米）
    OUTPUT_CRS = "EPSG:4326"  # 输出坐标系（经纬度）

    # ==========================
    # 采样参数
    # ==========================
    SAMPLE_SIZE = 1000  # 采样数量，None 为全部
    RANDOM_SEED = 42

    # ==========================
    # 几何处理参数
    # ==========================
    SIMPLIFY_TOLERANCE = 2  # 建筑简化容差（米）
    MIN_BUILDING_AREA = 20  # 最小建筑面积（平方米）

    # ==========================
    # 采样匹配参数
    # ==========================
    BUFFER_DISTANCE = 50  # 搜索缓冲区（米）
    MAX_DISTANCE = 100  # 最大有效距离（米）

    # ==========================
    # [新增] 道路筛选参数
    # ==========================
    # 是否开启道路类型筛选
    ROAD_FILTER_ENABLED = True

    # 道路数据中标识类型的字段名 (根据实际数据调整，常见为 'type', 'fclass', 'highway' 等)
    ROAD_TYPE_COLUMN = 'type'

    # 需要排除的道路类型列表
    EXCLUDED_ROAD_TYPES = [
        'motorway',  # 高速公路
        'motorway_link',  # 高速匝道
        'trunk',  # 干线
        'trunk_link',  # 干线匝道
        'pedestrian',  # 步行街（视情况而定，如果车进不去就排除）
        'footway',
        'steps'
    ]

    @staticmethod
    def print_config():
        """打印当前关键配置"""
        print("[配置信息]")
        print(f"  - 目标坐标系: {Config.TARGET_CRS}")
        print(f"  - 采样数量: {Config.SAMPLE_SIZE}")
        print(f"  - 道路筛选: {'开启' if Config.ROAD_FILTER_ENABLED else '关闭'}")
        if Config.ROAD_FILTER_ENABLED:
            print(f"  - 排除类型: {Config.EXCLUDED_ROAD_TYPES}")
        print("-" * 40)