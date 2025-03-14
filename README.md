# FloodEvacPlanner
- [English README](README.md)
- [中文 README](README_zh.md)

FloodEvacPlanner is an path planning algorithm and simulation system for evacuation planning in flood scenarios. 
The system integrates various algorithms to optimize escape routes and plans, aiming to assess and improve the efficiency and safety of evacuation processes during floods.

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
3. Run the main program: Use the main.py script to execute the evacuation planning task. Specify the configuration file with the -c argument.
```bash
python main.py -c config.yaml
```

## Configuration File

The project uses a YAML configuration file to customize the evacuation planning tasks. The configuration file allows you to specify parameters for the flood scenario, routing algorithms, and other settings. Below is an example of the `config.yaml` file:
```yaml
project_path: The root directory of your project where the code is located.
input_path: Directory containing the input data (e.g., shapefiles, GML files).
output_path: Directory where output files (e.g., simulation results, visualizations) will be saved.
logs_path: Directory for log files.

tasks_id: # A list of tasks to execute when running the code.
  - LOAD_ENV: Set to true to load the environment configuration. This step is mandatory.
  - VIS_ENV: Visualize the environment data.
  - RUN_ALGO: The algorithm to use for route planning. Choose from the following options: **Dijkstra**, **RRT**.
  - VIS_ROUTE: Set to true to visualize the route (generated `route_path` in previous tasks) or provide a custom route file path.
  - ANAL_ROUTE: Set to true to analyze the evacuation route or provide a custom route file path.

shp_files: # These are the raw data files located in the `input_path` directory.
  - map: The map of the research area (usually the boundary of a city).
  - buildings: Shapefile containing building polygons.
  - rivers: Shapefile containing river polygons.
  - floods: Shapefile containing flood area polygons, aligned with `flood_tag`.
  - roads: Shapefile containing the road network.
  - road_nodes: Shapefile containing road nodes, including start points (usually underground spaces), end points (usually shelters), and intersections.

gml_files: # Generated from `shp_files` to accelerate computation. If not available, they will be created.
  - graph: Roads and nodes data from `shp_files`.
  - flooded_graph: Roads and nodes data in a flooded environment (aligned with the `floods`). 

tags:
  - flood_tag: A tag to match the flood data with the task.
  - shelter_tag: A tag for identifying shelters in the evacuation plan.

random_seed: The seed value for random number generation to ensure reproducibility of the results.
```


## Data Description

- **floods & rivers** do not overlap. If there is any overlapping area, remove the overlapping portion from `floods`.
- **roads & road_nodes** are topological data. `roads` includes classification codes to identify different road types; `road_nodes` also contains node classifications, with `shelter_tag` used to identify selectable nodes (such as shelters).
- **graph & flooded_graph**: If gml files exist, the system will directly use these files to compute the route. Otherwise, gml files will be generated from `shp_files` and then used for route calculation.
