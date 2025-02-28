from enum import Enum


class NodeCodeMapping(Enum):
    n1 = (1.0, 'intersection', 'gray', 0.5)
    n2 = (2.0, 'intersection_new', 'gray', 0.5)
    n3 = (1283.0, 'space', 'red', 4)
    n4 = (8.0, 'shelter_zz', 'green', 8)
    n5 = (171.0, 'shelter_plan', 'green', 8)


    def __init__(self, code, description, color, size):
        # 每个code初始化时设定不同的属性
        self.code = code
        self.description = description
        self.color = color
        self.size = size

    @classmethod
    def get_description(cls, code):
        """根据code获取对应的属性"""
        for member in cls:
            if member.code == code:
                return member.description
        return None

    @classmethod
    def get_color(cls, code):
        """根据code获取对应的属性"""
        for member in cls:
            if member.code == code:
                return member.color
        return None

    @classmethod
    def get_size(cls, code):
        """根据code获取对应的属性"""
        for member in cls:
            if member.code == code:
                return member.size
        return None

    @classmethod
    def get_all_mappings(cls):
        """获取所有code映射"""
        return {member.code: (member.code, member.description, member.color, member.size) for member in cls}



class EdgeCodeMapping(Enum):
    # 定义各种code，给每个code配置不同的属性
    motorway = ('motorway', 7.0) # 高速公路 (7倍于 footway)
    motorway_link = ('motorway_link', 6.5)  # 高速公路连接
    trunk = ('trunk', 6.0)  # 干线连接
    trunk_link = ('trunk_link', 5.5)  # 干线连接
    primary = ('primary', 5.0)  # 主路
    primary_link = ('primary_link', 4.5)  # 主路连接
    secondary = ('secondary', 4.0)  # 次要道路
    secondary_link = ('secondary_link', 3.5)  # 次要路连接
    tertiary = ('tertiary', 3.0)  # 第三级道路
    tertiary_link = ('tertiary_link', 2.5)  # 第三级路连接
    living_street = ('living_street', 2.0)  # 生活街道
    residential = ('residential', 2.0)  # 住宅区道路
    service = ('service', 1.5)  # 服务道路
    cycleway = ('cycleway', 1.5)  # 自行车道
    unclassified = ('unclassified', 1.0)  # 未分类道路
    footway = ('footway', 1.0)  # 步道 (基准，宽度为1)
    path = ('path', 1.0)  # 小路
    pedestrian = ('pedestrian', 0.5)  # 步行道
    steps = ('steps', 0.5)  # 台阶


    def __init__(self, code, capacity):
        # 每个code初始化时设定不同的属性
        self.code = code
        self.capacity = capacity

    @classmethod
    def get_capacity(cls, code):
        """根据code获取对应的属性"""
        for member in cls:
            if member.code == code:
                return member.capacity
        return None

    @classmethod
    def get_all_mappings(cls):
        """获取所有code映射"""
        return {member.code: (member.code, member.capacity) for member in cls}
