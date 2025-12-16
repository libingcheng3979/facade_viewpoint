import time
from src.config import Config
from src.data_processor import DataProcessor
from src.sampler import Sampler
from src.visualizer import Visualizer


def main():
    print("=" * 50)
    print("   Facade Viewpoint Generator")
    print("=" * 50)

    Config.print_config()
    start_total = time.time()

    # --------------------------
    # 1. 数据加载与处理
    # --------------------------
    processor = DataProcessor(Config)
    buildings, roads = processor.run()

    # --------------------------
    # 2. 核心采样
    # --------------------------
    sampler = Sampler(Config)
    midpoints = sampler.generate_building_midpoints(buildings)
    raw_results = sampler.execute_sampling(buildings, roads, midpoints)

    if raw_results.empty:
        print("错误：未生成任何有效采样点，程序终止。")
        return

    # --------------------------
    # 3. 结果转换与可视化
    # --------------------------
    viz = Visualizer(Config)

    # 3.1 导出 CSV
    final_df = viz.save_results_to_csv(raw_results, "facade_points.csv")

    # 3.2 基础可视化
    viz.create_interactive_map(final_df, "preview_map.html")
    viz.plot_statistics(final_df, "report.png")

    # 3.3 绘制建筑简化对比图
    viz.plot_simplification_comparison(processor.simplification_samples)

    # 3.4 绘制采样详情图
    # 注意：raw_results 包含了 geometry 对象，适合用于绘图
    viz.plot_detailed_samples(raw_results, buildings, roads)

    # --------------------------
    # 结束
    # --------------------------
    elapsed = time.time() - start_total
    print("\n" + "=" * 50)
    print(f"全部任务完成！总耗时: {elapsed:.2f} 秒")
    print(f"请查看 data/output 目录下的 5 个结果文件")
    print("=" * 50)


if __name__ == "__main__":
    main()