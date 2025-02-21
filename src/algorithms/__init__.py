import numpy as np
import random
from shapely.geometry import Point, LineString
import geopandas as gpd
import os


# 计算两个点之间的欧几里得距离
def euclidean_distance(p1, p2):
    return np.linalg.norm(np.array(p1) - np.array(p2))


def step_condition(start, end, **kwargs):
    line = LineString([start, end])
    gdf = gpd.GeoDataFrame(geometry=[])

    map_data = kwargs.get('map_data', gdf)
    if not line.within(map_data.geometry.unary_union):
        return "map", map_data.geometry.unary_union

    floods = kwargs.get('floods', gdf)
    for flood in floods.geometry:
        if flood.intersects(line):  # 判断路径段是否与积水相交
            return "flood", flood

    shelter_circles = kwargs.get('shelter_circles', gdf)
    for shelter in shelter_circles.geometry:
        if shelter.intersects(line):  # 判断路径段是否与避难所相交
            return "shelter", shelter

    rivers = kwargs.get('rivers', gdf)
    for river in rivers.geometry:
        if river.intersects(line):  # 判断路径段是否与河流相交
            return "river", river

    buildings = kwargs.get('buildings', gdf)
    for building in buildings.geometry:
        if building.intersects(line):  # 判断路径段是否与建筑物相交
            return "building", building

    # 如果路径段没有经过障碍物或避难所
    return "pass", None


def is_connected(x, y):
    condition, obj = step_condition(x, y)
    if condition not in ["map", "river", "flood"]:
        return True
    return False


# 判断点是否在障碍物中
def is_in_obstacle(x, y, **kwargs):
    point = Point(x, y)
    gdf = gpd.GeoDataFrame(geometry=[])

    map_data = kwargs.get('map_data', gdf)
    if not map_data.geometry.unary_union.contains(point):
        logger.debug(f"Point({x},{y}) not in the map")
        return True

    floods = kwargs.get('floods', gdf)
    for geom in floods.geometry:
        if geom.contains(point):
            return True

    rivers = kwargs.get('rivers', gdf)
    for geom in rivers.geometry:
        if geom.contains(point):
            logger.debug(f"Point({x},{y}) in a river")
            return True

    return False

# 生成随机点
def generate_random_point(boundary):
    xmin, ymin, xmax, ymax = boundary
    while True:
        x = random.uniform(xmin, xmax)
        y = random.uniform(ymin, ymax)
        if not is_in_obstacle(x, y):  # 确保点不在障碍物中
            return (x, y)


