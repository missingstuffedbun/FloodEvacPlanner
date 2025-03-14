# FloodEvacPlanner

FloodEvacPlanner is an path planning algorithm and simulation system for evacuation planning in flood scenarios. 
The system integrates various algorithms to optimize escape routes and plans, aiming to assess and improve the efficiency and safety of evacuation processes during floods.

## Usage

### Running the Code
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

### Configuration File

The project uses a YAML configuration file to customize the evacuation planning tasks. The configuration file allows you to specify parameters for the flood scenario, routing algorithms, and other settings. Below is an example of the `config.yaml` file:
```yaml
project_path: The root directory of your project where the code is located.
input_path: Directory containing the input data (e.g., shapefiles, GML files).
output_path: Directory where output files (e.g., simulation results, visualizations) will be saved.
logs_path: Directory for log files.

tasks_id: 
- LOAD_ENV: Set to true to load the environment configuration.
- VIS_ENV: Visualize the environment data. 
- RUN_ALGO: The algorithm to use for route planning. Choose from the following options: **Dijkstra**, **RRT**. 
- VIS_ROUTE: Set to true to visualize the route (use route_path from the task or provide a custom file path)
- ANAL_ROUTE: Set to true if you want to analyze the evacuation route.

shp_files:
- map: The map of the flood scenario (e.g., map01.shp).
- buildings: Shapefile with building data (e.g., building01.shp).
- rivers: Shapefile with river data (e.g., river01.shp).
- floods:
- roads: The roads network shapefile (e.g., network03_v2.shp).
- road_nodes: The road nodes data (e.g., network_node04.shp).

gml_files: 
- graph: The initial graph used for routing (e.g., graph_0.gml).
- flooded_graph: The graph after flooding, which aligns with the flood data (e.g., graph_720.gml).

tags
- flood_tag: A tag to match the flood data with the task (e.g., 720).
- shelter_tag: A tag for identifying shelters in the evacuation plan (e.g., zz).

random_seed: The seed value for random number generation to ensure reproducibility of the results (e.g., 2025).
```
