from . import logger, input_path

import os
import geopandas as gpd


target_crs = 'EPSG:32649'

def load_shp(file_name):
    """
    加载一个 Shapefile 文件，并确保其转换为目标坐标参考系统（CRS）。
    """
    file_path = os.path.join(input_path, f"{file_name}")

    if not os.path.exists(file_path):
        logger.error(f"Shapefile {file_path} does not exist.")
        return None

    # 加载数据
    gdf = gpd.read_file(file_path)
    logger.info(f"Loaded data from {file_name}.shp with CRS {gdf.crs}")

    # 如果CRS不一致，转换坐标系统
    if gdf.crs != target_crs:
        logger.info(f"Reprojecting {file_name}.shp to {target_crs} CRS.")
        gdf = gdf.to_crs(target_crs)

    return gdf


def get_coords_from_points(geodataframe):
    """
    从 GeoDataFrame 中提取有效的点坐标。
    :param geodataframe: 包含空间数据的 GeoDataFrame
    :return: 有效点的坐标列表，每个坐标为 (x, y) 元组
    """
    # 提取有效点的坐标 (x, y)
    valid_coords = [(point.x, point.y) for point in geodataframe.geometry if point.is_valid]

    # 打印日志，输出有效点的数量
    logger.info(f"Number of valid points: {len(valid_coords)}")

    return valid_coords


def buffer_circles_from_points(geodataframe, radius):
    """
    从点数据创建缓冲区圆。
    :param geodataframe: 包含点数据的 GeoDataFrame
    :param radius: 缓冲区的半径（单位与点坐标一致）
    :return: 包含缓冲区圆的 GeoDataFrame
    """
    # 生成缓冲区圆
    buffered_circles = [point.buffer(radius) for point in geodataframe.geometry if point.is_valid]

    # 创建一个新的 GeoDataFrame 来存储缓冲区
    gdf = gpd.GeoDataFrame(geometry=buffered_circles)

    # 打印日志，输出生成的缓冲区数量
    logger.info(f"Generated {len(gdf)} buffer circles with radius {radius}")

    return gdf

