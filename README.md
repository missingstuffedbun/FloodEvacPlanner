# FloodEvacPlanner
- [English README](README.md)
- [中文 README](README_zh.md)

FloodEvacPlanner is an path planning algorithm and simulation system for evacuation planning in flood scenarios. 
The system integrates various algorithms to optimize escape routes and plans, aiming to assess and improve the efficiency and safety of evacuation processes during floods.

# Project Structure & Modules

```
FloodEvacPlanner/
├── src/
│   ├── main.py            # 程序入口：编排 环境→规划→Agent→可视化 全流程
│   ├── config_manager.py  # 配置单例：读取 YAML、创建带时间戳的输出目录、复制 config
│   ├── config.yaml        # 运行参数（路径、文件、算法、权重、开关）
│   ├── environment.py     # 环境建模：构建路网图、标记 shelter/crash 节点
│   ├── agent.py           # Agent 工厂：解析 OD 需求、生成并管理 agent
│   ├── planner.py         # 路径规划：drive / pedestrian / shelter 三类最短路
│   ├── visualize.py       # 可视化：基于 history.txt 生成交互式 HTML 地图
│   └── FloodEvacPlanner.code-workspace
├── output/<timestamp>/    # 每次运行的产物（history.txt, config.yaml 副本, evacuation_map.html）
├── requirements.txt
├── README.md / README_zh.md
└── LICENSE
```

| File | Module | Responsibility |
|---|---|---|
| `main.py` | **Orchestrator** | 解析 `-c` 参数；调用 `init_config`；构建 `Environment`、`Planner`、`AgentFactory`；把 agent 坐标 `snap` 到最近路网节点；逐 agent 跑三阶段规划循环；按 `params.visualize` 决定是否生成地图；配置 logging。 |
| `config_manager.py` | **Config (singleton)** | `Config` 单例 + `init_config()` / `get_config()`。读取 YAML（`utf-8`），自动创建 `output/<timestamp>/` 并把 timestamp 写入 `config['timestamp']`，同时复制所用 config 到该目录。 |
| `config.yaml` | **Config data** | 声明 `project_path` / `input_path` / `output_path`、`tags`、`algos`、`files`（5 个 shapefile）、`params`（crash_ratio、max_ped、max_shelter、random_seed、sample_size、max_replan、visualize）。详见下方 *Configuration File*。 |
| `environment.py` | **Environment** | 加载 5 个 shapefile 构建有向路网图 `G`（节点为 `(float, float)`）；派生 `G_vehicle`（仅 `car_access` 边）与 `G_pedestrian`（去 flooded 的无向视图）；标记 `shelter=True` 节点与按 `crash_ratio`+`random_seed` 随机阻塞的 `crash` 节点；提供 `get_shelters()`、`snap` 用的节点坐标。 |
| `agent.py` | **Agent / AgentFactory** | `AgentFactory.create_agents()` 从需求 shapefile 解析 OD 对（最多 `sample_size` 条），生成 `Agent` 对象；`Agent` 持有 `origin`/`destination`/`current_node`/`shelters`、历史 `history` 及 `add_history()` / `save_history()`（写入 `history.txt`，坐标保留 6 位小数）。 |
| `planner.py` | **Planner** | `plan_vehicle()`（开车，含 `_execute_vehicle` 边级阻断重规划）、`plan_pedestrian()`（步行到目的地）、`plan_shelter()`（multi-target dijkstra / rrt-prm 到最近 shelter）；`compute_vehicle_weights` / `compute_pedestrian_weights` 计算带惩罚的时空权重；路线按 `(start, end, mode)` 缓存。 |
| `visualize.py` | **Visualizer** | `build_map(history, config, out_html)` 读取 `history.txt` 与输入 shapefile，用 folium 绘制 agent 轨迹（蓝=到目的地 / 绿=到避难所 / 红=失败）以及 shelter/crash 点，输出 `evacuation_map.html`。支持命令行直接运行。 |

# Usage

## Running the Code
1. Clone the repo
```bash
git clone https://github.com/missingstuffedbun/FloodEvacPlanner.git
cd FloodEvacPlanner
```
2. Install dependencies
```bash
pip install -r requirements.txt
```
3. Run the main program. It accepts an optional `-c/--config` argument; when omitted it defaults to `src/config.yaml`:
```bash
python src/main.py                                   # uses src/config.yaml
python src/main.py -c path/to/your_config.yaml       # use a custom config
```

## Configuration File (`src/config.yaml`)

The configuration is read once at startup via `config_manager.init_config()` and exposed as a singleton through `get_config()`. `config_manager` also creates a timestamped output folder `output/<YYYYMMDDHHMMSS>/`, copies the used config there, and stores the timestamp in `config['timestamp']`.

Below is the **actual** structure used by the code (field names differ from older docs):

```yaml
project_path: 'D:\coding\FloodEvacPlanner'   # absolute root; all relative input paths are resolved against this
input_path:   'input'                         # input shapefiles directory, relative to project_path
output_path:  'output'                        # base output directory; real results go to output/<timestamp>/
logs_path:    'logs'                          # log directory

tags:
  flood_tag:   '1974'                         # selects the flooded-edges shapefile (see files.edges_flood)
  crash_tag:   'low'                          # descriptive tag for the crash scenario
  traffic_tag: 'wd_am_off_peak'               # descriptive tag for the destination/traffic scenario

algos:
  algo1: 'dijkstra'          # routing algorithm for the vehicle (drive) stage
  algo2: 'dijkstra'          # routing algorithm for the pedestrian-to-destination stage
  algo3: 'multi-dijkstra'    # routing algorithm for the pedestrian-to-shelter stage
  weight1: 'time'            # edge weight for algo1 (time | length)
  weight2: 'length'          # edge weight for algo2 (time | length)
  weight3: 'length'          # edge weight for algo3 (time | length)

files:                        # shapefile names, all located in input_path
  edges_all:    'Edges.shp'             # full road network
  edges_flood:  'edges_197401.shp'      # flooded subset, must be a subset of edges_all; aligned with tags.flood_tag
  crash:        'crash.shp'             # candidate crash points
  traffic:      'destinations_wd_am_off_peak.shp'  # origin/destination demand points; aligned with tags.traffic_tag
  shelter:      'shelter_snap.shp'      # shelter locations

params:
  crash_ratio:  0.1     # 0~1, fraction of crash_points randomly marked as blocked nodes
  max_ped:      5000    # max pedestrian routing distance (meters) considered reachable
  max_shelter:  3000    # max distance (meters) to a shelter considered reachable
  random_seed:  2025    # seed for reproducible crash-node sampling and any random sampling
  sample_size:  200     # number of origin-destination pairs to sample from the demand file
  max_replan:   10      # max drive-stage replanning attempts before falling back to shelter
  visualize:    true    # if true, auto-generate an interactive HTML map after planning (see Output)
```

### How each parameter is used in `main.py` / `environment.py`

| Parameter | Where read | Effect |
|---|---|---|
| `project_path`, `input_path`, `files.*` | `environment.py __init__` | Builds absolute paths to load the 5 shapefiles that construct the road graph. |
| `tags.flood_tag` | `environment.py` (via `files.edges_flood`) | Names the flooded-edges file; asserted to be a geometric subset of `edges_all`. |
| `params.crash_ratio` | `environment.py _mark_crash` | `num_crash = int(len(crash_points) * crash_ratio)` nodes are randomly blocked. |
| `params.random_seed` | `environment.py _mark_crash` | `np.random.seed(...)` so crash sampling is reproducible. |
| `params.max_replan` | `main.py` (line ~72) | Bounds the `while` loop of the drive stage: `while ... and max_replan > 0`. |
| `params.sample_size` | `agent.py AgentFactory.create_agents` | Caps how many OD pairs are sampled from the demand shapefile. |
| `params.max_ped` / `params.max_shelter` | `planner.py` (pedestrian / shelter routing) | Distance thresholds deciding whether a pedestrian route is reachable. |
| `algos.*` | `planner.py` | Selects the algorithm and edge weight for each of the three planning stages. |
| `output_path` + `timestamp` | `main.py` (line ~107) | History is written to `output/<timestamp>/history.txt`. |
| `params.visualize` | `main.py` (line ~110) | When `true`, calls `visualize.build_map(...)` to render `output/<timestamp>/evacuation_map.html`. |

> Note: `logs_path` is reserved for log output; the current run logs to stdout via `logging.basicConfig`. `tags.crash_tag` / `tags.traffic_tag` are descriptive labels (documentation only) — the actual data files are chosen through `files.crash` / `files.traffic`.

## Evacuation Task Logic

This section describes exactly what `python src/main.py` does at runtime. The pipeline is **Environment → Planner → Agents → (optional) Visualizer**.

### 1. Build the environment (`environment.py`)
- Loads the 5 shapefiles under `input_path` (`edges_all`, `edges_flood`, `crash`, `traffic`, `shelter`) to build a directed road-network graph `G` (nodes are `(float, float)` coordinate tuples).
- Derives two filtered views:
  - `G_vehicle` — only edges with `car_access` (used for the drive stage).
  - `G_pedestrian` — undirected view excluding `flooded` edges (used for walking stages).
- Marks nodes:
  - `shelter=True` on the graph node nearest each shelter point.
  - `crash=True` on `int(len(crash_points) * crash_ratio)` randomly chosen nodes (seeded by `random_seed`). These nodes become impassable / high-penalty for routing.

### 2. Prepare agents (`agent.py`)
- `AgentFactory` reads the demand shapefile (`files.traffic`) and parses `ORIGIN_X/ORIGIN_Y` → origin and the geometry point → destination, yielding one OD pair per record.
- For every agent, the origin/destination coordinates are **snapped** to the nearest graph node (via `cKDTree` in `main.py`) so routing always starts/ends on a real node.
- Each agent carries `current_node` and the list of shelter nodes.

### 3. Plan a route per agent (`main.py` + `planner.py`)
For each agent, a **three-stage fallback** is attempted:

**Stage 1 — Drive (`plan_vehicle`)**
- Runs in a `while` loop bounded by `params.max_replan`.
- Computes a drive route from `current_node` to the agent's `destination` on `G_vehicle` using `algo1` (`dijkstra`/`astar`) with weight `vehicle_<weight1>`.
- `_execute_vehicle` walks the route edge-by-edge; if it hits a `blocked` / `flooded` edge or a `crash` node, that edge is marked `blocked` and the agent **stops early** (`stop_sig=False`), then replans from the stop node.
- If the full route is traversable, `stop_sig=True` → agent has **reached destination** and Stage 1 ends successfully.
- If no drive route exists at all (`route is None`), Stage 1 is abandoned and the agent falls through to the shelter decision.

**Decision — destination or shelter? (`destination_or_shelter` in `main.py`)**
- Compares straight-line distance from `current_node` to the original `destination` vs. to the nearest shelter (using `max_distance=3000` m default).
- Returns `'destination'` if the destination is within 3000 m **or** closer than the nearest shelter; otherwise `'shelter'`.

**Stage 2 — Walk to destination (`plan_pedestrian`)**
- If the decision is `'destination'`: route on `G_pedestrian` from `current_node` to the original `destination` using `algo2` with weight `pedestrian_<weight2>`. If reachable, the agent **reaches destination**.

**Stage 3 — Walk to shelter (`plan_shelter`)**
- If the decision is `'shelter'`: run `multi_target_dijkstra` (or `rrt-prm` per `algo3`) from `current_node` to the **nearest reachable shelter** on `G_pedestrian`. If reachable, the agent **reaches shelter**.

**Fallback**
- If an agent ends with no recorded path at all (e.g. starts with no route), a `failed` history segment is appended so `history.txt` is never empty.

### 4. Record history
- Every agent appends one or more segments `{mode: vehicle|pedestrian|failed, exec_route: [[lon,lat],...], stop_sig: bool}` to `history.txt` in `output/<timestamp>/` (node coords rounded to 6 decimals).

### 5. Visualize (optional)
- If `params.visualize: true`, `visualize.build_map(...)` renders `evacuation_map.html` from `history.txt` + the input shapefiles (see Output).

### Weight models (in `planner.py`)
- `compute_vehicle_weights`: edge cost = travel time, inflated by lane count, `crash` node (+0.3), `flooded` edge (+0.6), and `special_ro` (+0.1). Length is inflated by crash/flood penalties.
- `compute_pedestrian_weights`: walking time at ~1.5 m/s, inflated near high-speed roads (+0.2) and `special_ro` (+0.3).

> Note: route results are cached per `(start, end, mode)` inside `Planner`, so repeated queries for the same OD are computed once.

## Output

Each run writes to a fresh `output/<timestamp>/` folder:

- `history.txt` — one JSON line per agent; each line is a list of segments `{mode, exec_route, stop_sig}` describing the driven/pedestrian path (or a `failed` record).
- `config.yaml` — a copy of the config used for that run.
- `evacuation_map.html` — **only if `params.visualize: true`**; interactive folium map plotting agent trajectories (blue = reached destination, green = reached shelter, red = failed), plus shelter (green) and crash (red) points.

You can also generate the map for an existing `history.txt` without re-running planning:
```bash
python src/visualize.py                      # uses latest output/<timestamp>/history.txt
python src/visualize.py <history.txt> <config.yaml> <output.html>   # explicit paths
```
(Requires `pip install folium`.)


## Data Description

- **floods & rivers** do not overlap. If there is any overlapping area, remove the overlapping portion from `floods`.
- **roads & road_nodes** are topological data. `roads` includes classification codes to identify different road types; `road_nodes` also contains node classifications, with `shelter_tag` used to identify selectable nodes (such as shelters).
- **graph & flooded_graph**: If gml files exist, the system will directly use these files to compute the route. Otherwise, gml files will be generated from `shp_files` and then used for route calculation.
