
# Facade Viewpoint

为解决城市计算中街景数据获取的视点定位问题，确保采集的图像能够正对建筑沿街主立面，本项目提出一种自动化方法，根据建筑足迹和路网数据，批量生成面向建筑立面的最佳街景采样点（Lat, Lon）及相机拍摄角度（heading）。

<img width="4271" height="1763" alt="streetview_samples_examples" src="https://github.com/user-attachments/assets/bba58441-ae41-4062-9c14-fde4153336b7" />

## 主要功能

* **建筑优化**：自动修复几何拓扑错误，过滤噪点建筑，并基于 Douglas-Peucker 算法对建筑轮廓进行简化。
* **道路筛选**：支持按道路类型（如 type/fclass）自动剔除高速公路、高架桥、步行道等不适合街景车采集的道路。
* **视点定位与角度计算**：基于建筑特征边中点与路网的空间关系，计算最近邻投影点，生成最优采样位置，并计算相机朝向。
* **可视化验证**：生成采样详情图、交互式网页地图及统计图表。

<img width="700" height="400" alt="img_1" src="https://github.com/user-attachments/assets/953a296c-211a-42b8-bc8e-6ebb845aa9c8" />

## 快速开始

### 1. 环境依赖

本项目基于 Python 3.10 开发。

```bash
git clone [https://github.com/libingcheng3979/facade_viewpoint.git](https://github.com/libingcheng3979/facade_viewpoint.git)
cd facade_viewpoint
pip install -r requirements.txt
```

### 2. 数据准备

请确保拥有以下格式的 GeoJSON 数据（坐标系建议预先统一，或依赖程序的自动投影）：

* 建筑轮廓数据（Polygon/MultiPolygon）
* 道路网络数据（LineString）

### 3. 参数配置

打开 `src/config.py` 修改文件路径及核心参数：

```python
# 输入数据路径
BUILDING_PATH = r"path/to/your/buildings.geojson"
ROAD_PATH = r"path/to/your/roads.geojson"

# 核心参数
ROAD_FILTER_ENABLED = True           # 开启道路类型筛选
EXCLUDED_ROAD_TYPES = ['motorway', 'trunk', 'footway'] # 需要排除的道路类型
SIMPLIFY_TOLERANCE = 2               # 建筑简化容差(米)
BUFFER_DISTANCE = 50                 # 搜索半径(米)
```

### 4. 项目运行
```bash
python main.py
```

## 输出结果

程序运行完成后，结果将保存在 `data/` 目录下：

| 文件名 | 说明 |
| --- | --- |
| **facade_points.csv** | 包含采样点经纬度、Heading、距离、置信度等核心结果 |
| **preview_map.html** | 交互式网页地图，用于宏观查看采样分布 |
| **streetview_samples_examples.png** | 采样详情示意图 |
| **building_simplification_comparison.png** | 建筑轮廓简化前后的效果对比 |
| **report.png** | 距离、角度及置信度的统计分布图 |

## 参考资料

> Sun, M., Zhang, F., Duarte, F., & Ratti, C. (2022). Understanding architecture age and style through deep learning. *Cities*, 128, 103787.

## 声明

本方法仅供个人科研学习使用，请勿用于任何非科研和非法用途。

有任何疑问欢迎联系交流 (libingcheng3979@163.com)

