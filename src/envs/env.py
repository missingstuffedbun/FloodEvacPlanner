class eEnvironment:
    def __init__(self, files):
        """
        初始化洪灾逃生环境配置类，传入文件路径配置字典。
        :param files: 配置字典，包含文件路径的键值对。
        """
        # 初始化文件配置字典，便于后续访问
        self.files = files

    def __getattr__(self, item):
        """
        动态获取配置项的值。如果项不存在，返回 None。
        :param item: 配置项的名称（如 'spaces'，'shelters' 等）
        :return: 配置项的值，如果不存在则返回 None
        """
        return self.files.get(item, None)
