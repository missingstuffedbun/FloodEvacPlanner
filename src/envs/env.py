from src.envs.graph import load_graph, remove_flooded_edges, build_road_graph
from src.envs.shp import load_shp, get_coords_from_points, buffer_circles_from_points
from src.utils.config import ConfigSingleton
from src.utils.log import LoggerSingleton

import os
import geopandas as gpd
from shapely.geometry import Point, LineString


logger = LoggerSingleton().get_logger()
config = ConfigSingleton().get_config()
input_path = config.input_path
output_path = config.output_path
shp_files = config.shp_files
gml_files = config.gml_files


class Environment:
    def __init__(self):
        # 使用 load_shp 根据配置文件加载数据，并赋值给相应的属性
        self.shelters = load_shp(os.path.join(input_path, shp_files.get('shelters', '')))
        self.spaces = load_shp(os.path.join(input_path, shp_files.get('spaces', '')))
        self.map = load_shp(os.path.join(input_path, shp_files.get('map', '')))
        self.buildings = load_shp(os.path.join(input_path, shp_files.get('buildings', '')))
        self.rivers = load_shp(os.path.join(input_path, shp_files.get('rivers', '')))
        self.roads = load_shp(os.path.join(input_path, shp_files.get('roads', '')))
        self.road_nodes = load_shp(os.path.join(input_path, shp_files.get('road_nodes', '')))
        self.floods = load_shp(os.path.join(input_path, shp_files.get('floods', '')))
        # 使用 load_graph 根据配置文件加载数据，并赋值给相应的属性
        self.graph = load_graph(os.path.join(input_path, gml_files.get('graph', '')))
        self.flooded_graph = load_graph(os.path.join(input_path, gml_files.get('flooded_graph', '')))


    def __getattr__(self, item):
        """
        动态获取配置项的值。如果项不存在，返回 None。
        :param item: 配置项的名称（如 'spaces'，'shelters' 等）
        :return: 配置项的值，如果不存在则返回 None
        """
        return self.files_data.get(item, None)

    def preprocessing(self):
        self.remove_shelters_in_rivers()
        self.shelters_coords = get_coords_from_points(self.shelters)
        self.shelter_circles = buffer_circles_from_points(self.shelters_coords, radius=100)
        self.spaces_coords = get_coords_from_points(self.spaces)
        if self.floods is not None:
            self.clip_flood()


    def graph_for_Dijkstra(self):
        if self.flooded_graph is not None:
            self.graph_Dijkstra = self.flooded_graph
        elif self.graph is not None:
            self.graph_Dijkstra = remove_flooded_edges(G=self.graph, floods=self.floods)
        else:
            self.graph_Dijkstra = build_road_graph(edges=self.roads, nodes=self.road_nodes)


    def remove_shelters_in_rivers(self):
        # 创建一个掩码，检查每个庇护所是否位于河流的多边形内
        shelters_in_rivers = self.shelters[
            self.shelters.geometry.apply(lambda x: any(x.within(river) for river in self.rivers.geometry))]
        # 输出日志，记录有多少个庇护所点被移除
        logger.debug(f"Removed {len(shelters_in_rivers)} shelters located within rivers.")
        # 从原始庇护所中移除这些点
        shelters_filtered = self.shelters[~self.shelters.index.isin(shelters_in_rivers.index)]
        self.shelters = shelters_filtered

    def clip_flood(self):
        # 执行洪灾区域剪裁
        floods_clipped = gpd.overlay(self.floods, self.rivers, how='difference')
        logger.debug(f"Flood area: {self.floods.geometry.area.sum()} -> {floods_clipped.geometry.area.sum()}")
        self.floods = floods_clipped

    def step_condition(self, start, end):
        line = LineString([start, end])
        gdf = gpd.GeoDataFrame(geometry=[])
    
        if not line.within(self.map.geometry.unary_union):
            return "map", self.map.geometry.unary_union
    
        for flood in self.floods.geometry:
            if flood.intersects(line):  # 判断路径段是否与积水相交
                return "flood", flood
    
        for shelter in self.shelter_circles.geometry:
            if shelter.intersects(line):  # 判断路径段是否与避难所相交
                return "shelter", shelter
    
        for river in self.rivers.geometry:
            if river.intersects(line):  # 判断路径段是否与河流相交
                return "river", river
    
        for building in self.buildings.geometry:
            if building.intersects(line):  # 判断路径段是否与建筑物相交
                return "building", building
    
        # 如果路径段没有经过障碍物或避难所
        return "pass", None

    
    def is_connected(self, x, y):
        condition, obj = self.step_condition(x, y)
        if condition not in ["map", "river", "flood"]:
            return True
        return False


    # 判断点是否在障碍物中
    def is_in_obstacle(self, x, y):
        point = Point(x, y)
    
        if not self.map.geometry.unary_union.contains(point):
            logger.debug(f"Point({x},{y}) not in the map")
            return True
    
        for geom in self.floods.geometry:
            if geom.contains(point):
                logger.debug(f"Point({x},{y}) in a flooded area")
                return True
    
        for geom in self.rivers.geometry:
            if geom.contains(point):
                logger.debug(f"Point({x},{y}) in a river")
                return True
        return False

    # 生成随机点
    def generate_random_point(self):
        xmin, ymin, xmax, ymax = self.map.geometry.unary_union.envelope
        while True:
            x = random.uniform(xmin, xmax)
            y = random.uniform(ymin, ymax)
            if not self.is_in_obstacle(x, y):  # 确保点不在障碍物中
                return (x, y)

    
