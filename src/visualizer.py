import os
import geopandas as gpd
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import folium
from shapely.geometry import Point, MultiPolygon, Polygon
from .config import Config
from .geometry_utils import calculate_polygon_edge_midpoints  # 引入计算工具

# 设置 matplotlib 中文支持
plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False


class Visualizer:
    def __init__(self, config=Config):
        self.cfg = config

    def save_results_to_csv(self, results_df, output_filename="streetview_samples.csv"):
        """将结果转换为 WGS84 坐标并保存为 CSV"""
        print(f"\n正在导出结果到 {output_filename}...")

        # 1. 坐标转换
        gdf_sample = gpd.GeoDataFrame(results_df, geometry='geometry_sample', crs=self.cfg.TARGET_CRS).to_crs(
            self.cfg.OUTPUT_CRS)
        gdf_midpoint = gpd.GeoDataFrame(results_df, geometry='geometry_midpoint', crs=self.cfg.TARGET_CRS).to_crs(
            self.cfg.OUTPUT_CRS)

        # 2. 提取经纬度
        final_df = results_df.copy()
        final_df['lat'] = gdf_sample.geometry.y
        final_df['lng'] = gdf_sample.geometry.x
        final_df['building_center_lat'] = gdf_midpoint.geometry.y
        final_df['building_center_lng'] = gdf_midpoint.geometry.x

        # 3. 添加 PID 字段 (0, 1, 2...)
        final_df['PID'] = range(len(final_df))

        # 4. 清理列
        cols_to_drop = ['geometry_sample', 'geometry_midpoint']
        final_df = final_df.drop(columns=[c for c in cols_to_drop if c in final_df.columns])

        # 5. 定义输出顺序 (将 PID 放在第一位)
        ordered_cols = ['PID', 'building_id', 'lat', 'lng', 'heading', 'distance', 'confidence',
                        'building_area', 'building_center_lat', 'building_center_lng', 'edge_index']

        # 筛选存在的列并排序
        final_df = final_df[[c for c in ordered_cols if c in final_df.columns]]

        # 6. 保存
        output_path = os.path.join("data", output_filename)
        os.makedirs("data", exist_ok=True)
        final_df.to_csv(output_path, index=False, encoding='utf-8-sig')
        print(f"  ✓ CSV 保存成功: {output_path}")
        return final_df

    def create_interactive_map(self, final_df, output_filename="map_preview.html"):
        """生成 Folium 交互式地图 (保持原样)"""
        print("\n正在生成交互式地图...")
        if final_df.empty: return

        display_limit = 100
        plot_data = final_df.sample(n=display_limit, random_state=self.cfg.RANDOM_SEED) if len(
            final_df) > display_limit else final_df

        center_lat = plot_data['lat'].mean()
        center_lng = plot_data['lng'].mean()

        m = folium.Map(location=[center_lat, center_lng], zoom_start=15, tiles='OpenStreetMap')

        for _, row in plot_data.iterrows():
            folium.CircleMarker(
                location=[row['lat'], row['lng']], radius=5, color='blue', fill=True, fill_opacity=0.7,
                popup=f"Heading: {row['heading']}°<br>Dist: {row['distance']}m",
                tooltip=f"PID: {row.get('building_id')}"
            ).add_to(m)
            folium.CircleMarker(
                location=[row['building_center_lat'], row['building_center_lng']], radius=3, color='red', fill=True,
                fill_opacity=0.5
            ).add_to(m)
            folium.PolyLine(
                locations=[[row['lat'], row['lng']], [row['building_center_lat'], row['building_center_lng']]],
                color='green', weight=1, opacity=0.6
            ).add_to(m)

        output_path = os.path.join("data/output", output_filename)
        m.save(output_path)
        print(f"  地图已保存: {output_path}")

    def plot_statistics(self, df, output_filename="statistics.png"):
        """绘制统计图表 (保持原样)"""
        print("\n正在生成统计图表...")
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))

        axes[0, 0].hist(df['distance'], bins=30, color='steelblue', edgecolor='black', alpha=0.7)
        axes[0, 0].set_title('采样距离分布 (米)')

        axes[0, 1].hist(df['heading'], bins=36, color='orange', edgecolor='black', alpha=0.7)
        axes[0, 1].set_title('Heading 角度分布')

        axes[1, 0].hist(df['confidence'], bins=30, color='green', edgecolor='black', alpha=0.7)
        axes[1, 0].set_title('置信度分布')

        scatter = axes[1, 1].scatter(df['building_area'], df['distance'], c=df['confidence'], cmap='RdYlGn', alpha=0.6,
                                     s=15)
        axes[1, 1].set_title('建筑面积 vs 采样距离')
        plt.colorbar(scatter, ax=axes[1, 1], label='置信度')

        plt.tight_layout()
        output_path = os.path.join("data/output", output_filename)
        plt.savefig(output_path, dpi=300)
        print(f"  统计图已保存: {output_path}")

    # =========================================================================
    # 建筑简化对比图
    # =========================================================================
    def plot_simplification_comparison(self, samples_dict, output_filename="building_simplification_comparison.png"):
        """
        绘制简化前后的对比图
        Args:
            samples_dict: 包含 'original' 和 'simplified' 两个 GeoDataFrame 的字典
        """
        print("\n正在生成简化效果对比图...")

        original_gdf = samples_dict.get('original')
        simplified_gdf = samples_dict.get('simplified')

        if original_gdf is None or simplified_gdf is None:
            print("  缺少样本数据，跳过简化对比图生成。")
            return

        # 确保按 ID 排序以对应
        original_gdf = original_gdf.sort_values('building_id')
        simplified_gdf = simplified_gdf.sort_values('building_id')

        ids = original_gdf['building_id'].values
        fig, axes = plt.subplots(1, len(ids), figsize=(6 * len(ids), 6))
        if len(ids) == 1: axes = [axes]  # 兼容只有1个样本的情况

        def get_vertex_count(geom):
            if geom.geom_type == 'Polygon':
                return len(geom.exterior.coords)
            elif geom.geom_type == 'MultiPolygon':
                return sum(len(g.exterior.coords) for g in geom.geoms)
            return 0

        for ax, bid in zip(axes, ids):
            orig_row = original_gdf[original_gdf['building_id'] == bid].iloc[0]
            simp_row = simplified_gdf[simplified_gdf['building_id'] == bid].iloc[0]

            # 统计顶点
            v_orig = get_vertex_count(orig_row.geometry)
            v_simp = get_vertex_count(simp_row.geometry)
            reduction = (1 - v_simp / v_orig) * 100

            # 绘制原始（蓝色实线）
            if orig_row.geometry.geom_type == 'MultiPolygon':
                for poly in orig_row.geometry.geoms:
                    x, y = poly.exterior.xy
                    ax.plot(x, y, 'b-', linewidth=3, alpha=0.5, label='Original')
            else:
                x, y = orig_row.geometry.exterior.xy
                ax.plot(x, y, 'b-', linewidth=3, alpha=0.5, label='Original')

            # 绘制简化（红色虚线）
            if simp_row.geometry.geom_type == 'MultiPolygon':
                for poly in simp_row.geometry.geoms:
                    x, y = poly.exterior.xy
                    ax.plot(x, y, 'r--', linewidth=2, label='Simplified')
            else:
                x, y = simp_row.geometry.exterior.xy
                ax.plot(x, y, 'r--', linewidth=2, label='Simplified')

            ax.set_title(f"Building #{bid}\n顶点: {v_orig} → {v_simp} (Reduced {reduction:.1f}%)")
            ax.set_aspect('equal')
            ax.grid(True, alpha=0.3)
            # 避免图例重复
            handles, labels = ax.get_legend_handles_labels()
            by_label = dict(zip(labels, handles))
            ax.legend(by_label.values(), by_label.keys())

        plt.tight_layout()
        output_path = os.path.join("data/output", output_filename)
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"  简化对比图已保存: {output_path}")

    # =========================================================================
    # 采样详情图
    # =========================================================================
    def plot_detailed_samples(self, results_df, buildings_gdf, roads_gdf,
                              output_filename="streetview_samples_examples.png"):
        """
        绘制详细的采样示意图
        特点：保持特写视角，仅显示视野内的道路片段，标出所有边中点
        """
        print("\n正在生成采样详情图...")

        if results_df.empty: return

        # 随机选择 3 个采样结果
        sample_indices = np.random.choice(len(results_df), size=min(3, len(results_df)), replace=False)
        sample_rows = results_df.iloc[sample_indices]

        fig, axes = plt.subplots(1, 3, figsize=(18, 6))
        if len(sample_rows) == 1: axes = [axes]

        for ax, (_, row) in zip(axes, sample_rows.iterrows()):
            bid = row['building_id']

            # 1. 获取核心几何对象
            building_geom = buildings_gdf[buildings_gdf['building_id'] == bid].geometry.iloc[0]
            sample_pt = row['geometry_sample']  # 采样点 Point
            target_pt = row['geometry_midpoint']  # 目标中点 Point

            # 2. 计算边界 (Focus Box)
            # 创建一个临时的 GeoSeries 来计算边界
            temp_geo = gpd.GeoSeries([building_geom, sample_pt])
            minx, miny, maxx, maxy = temp_geo.total_bounds

            # 计算边距 (Padding)，比如取宽高的 20% 作为留白
            dx = maxx - minx
            dy = maxy - miny
            padding = max(dx, dy) * 0.2

            view_xlim = (minx - padding, maxx + padding)
            view_ylim = (miny - padding, maxy + padding)

            # 3. 获取并裁剪附近的道路 (用于背景)
            # 先用一个稍微大一点的 buffer 查路，确保路不断开
            search_buffer = building_geom.buffer(self.cfg.BUFFER_DISTANCE)
            possible_roads_idx = list(roads_gdf.sindex.query(search_buffer, predicate='intersects'))
            nearby_roads = roads_gdf.iloc[possible_roads_idx]

            # --- 开始绘图 ---

            # A. 绘制道路 (灰色粗线，作为背景)
            # 不需要裁剪几何，直接画，然后通过 set_xlim 裁剪视野
            if not nearby_roads.empty:
                nearby_roads.plot(ax=ax, color='#D3D3D3', linewidth=4, alpha=0.6, label='Road', zorder=1)

            # B. 绘制建筑 (淡蓝色填充 + 蓝色边框)
            if building_geom.geom_type == 'MultiPolygon':
                for poly in building_geom.geoms:
                    x, y = poly.exterior.xy
                    ax.fill(x, y, '#E1F5FE', alpha=1.0, edgecolor='#0277BD', linewidth=2, zorder=2)
            else:
                x, y = building_geom.exterior.xy
                ax.fill(x, y, '#E1F5FE', alpha=1.0, edgecolor='#0277BD', linewidth=2, zorder=2)

            # C. 绘制所有候选边中点 (灰色小空心点)
            # 实时计算该建筑的所有中点
            all_midpoints = calculate_polygon_edge_midpoints(building_geom)
            mx = [m['midpoint'].x for m in all_midpoints]
            my = [m['midpoint'].y for m in all_midpoints]
            ax.scatter(mx, my, c='white', edgecolors='gray', s=35, zorder=3, label='Edges', marker='o', linewidth=1)

            # D. 绘制选定的最佳中点 (红色实心点)
            ax.scatter([target_pt.x], [target_pt.y], c='#D50000', s=80, zorder=4, label='Target', edgecolors='white')

            # E. 绘制采样点 (蓝色实心点)
            ax.scatter([sample_pt.x], [sample_pt.y], c='#2962FF', s=100, zorder=4, label='Sample', edgecolors='white')

            # F. 绘制箭头 (绿色)
            ax.annotate('',
                        xy=(target_pt.x, target_pt.y),
                        xytext=(sample_pt.x, sample_pt.y),
                        arrowprops=dict(arrowstyle='->', color='#00C853', lw=2.5),
                        zorder=5)

            # G. 强制锁定视角范围
            ax.set_xlim(view_xlim)
            ax.set_ylim(view_ylim)

            # 设置标题和样式
            ax.set_title(
                f'Building #{bid}\n'
                f'Heading: {row["heading"]:.1f}° | Dist: {row["distance"]:.1f}m',
                fontsize=9, pad=10
            )
            # 隐藏坐标轴刻度，让图更清爽
            ax.set_xticks([])
            ax.set_yticks([])
            ax.set_aspect('equal')

            # 简单的图例
            handles, labels = ax.get_legend_handles_labels()
            by_label = dict(zip(labels, handles))
            ax.legend(by_label.values(), by_label.keys(), loc='best', fontsize=7, framealpha=0.8)

        plt.tight_layout()
        output_path = os.path.join("data/output", output_filename)
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"  详情图已保存: {output_path}")
