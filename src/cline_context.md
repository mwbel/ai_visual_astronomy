这是一个天文学可视化项目，使用 Python 开发。

【环境约束】
1. Python 解释器必须使用当前工作区的 .venv。
2. 严禁联网下载星历文件；只能从本地 de421.bsp 加载。
   - 使用 Path(__file__).parent / 'de421.bsp' 指定路径。
3. 依赖库固定为：numpy、matplotlib、plotly、astropy、skyfield（已安装）。
4. 所有脚本必须兼容 Python 3.11。

【代码规范】
1. 遵守 PEP8 风格，必要时加注释。
2. 文件结构：
   - 根目录：放置 demo 脚本（如 astro_demo.py, astro_orbits.py）
   - 后续可建 src/ 放置工具函数
3. 生成的代码应包含运行示例说明（命令行方式）。
4. 绘图要求：
   - matplotlib：包含标题、坐标轴标签、图例、网格，比例合适。
   - plotly（可选）：支持交互缩放与悬浮提示。

【功能需求常见示例】
- 扩展已有 astro_demo.py，绘制多个行星轨道。
- 新建脚本，支持 CLI 参数（年份、行星列表、采样粒度）。
- 输出 2D 或 3D 轨道投影图。
- 提示“请确保 de421.bsp 在项目根目录”而不是尝试联网。

【交互要求】
- 在给出新脚本时，请标注运行方式，例如：
  python astro_orbits.py --year 2024 --planets earth,mars --step monthly
 @