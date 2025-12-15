import geopandas as gpd
from src.config import cfg
from src.data_loader import load_and_preprocess_data
from src.processor import StreetViewSampler
from src.visualizer import generate_visualizations

def main():
    print("=" * 80)
    print("街道建筑立面图片采样点生成系统")
    print("=" * 80)
    
    try:
        # 1. 加载数据
        buildings, roads = load_and_preprocess_data()
        
        # 2. 核心处理
        sampler = StreetViewSampler(buildings, roads)
        results_df = sampler.generate_points()
        
        # 3. 后处理 (坐标转换回 WGS84 用于输出)
        if not results_df.empty:
            print(f"\n 将结果转换回 {cfg.OUTPUT_CRS}...")
            
            # 创建几何列以便转换
            gdf_samples = gpd.GeoDataFrame(
                results_df, 
                geometry=gpd.points_from_xy(results_df.sample_point_x, results_df.sample_point_y),
                crs=cfg.TARGET_CRS
            )
            gdf_centers = gpd.GeoDataFrame(
                results_df, 
                geometry=gpd.points_from_xy(results_df.building_center_x, results_df.building_center_y),
                crs=cfg.TARGET_CRS
            )
            
            samples_wgs = gdf_samples.to_crs(cfg.OUTPUT_CRS)
            centers_wgs = gdf_centers.to_crs(cfg.OUTPUT_CRS)
            
            results_df['lat'] = samples_wgs.geometry.y
            results_df['lng'] = samples_wgs.geometry.x
            results_df['building_lat'] = centers_wgs.geometry.y
            results_df['building_lng'] = centers_wgs.geometry.x
        
        # 4. 可视化与导出
        generate_visualizations(results_df)
        
        print("\n 程序执行完毕！")
        
    except Exception as e:
        print(f"\n 发生错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
