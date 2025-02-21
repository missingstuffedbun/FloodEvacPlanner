import numpy as np


# 计算两个点之间的欧几里得距离
def euclidean_distance(p1, p2):
    return np.linalg.norm(np.array(p1) - np.array(p2))
