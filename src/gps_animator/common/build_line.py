import queue
from repairing_gpd import build_filtered_dataframe, connect_lines
import geopandas as gpd
import osmnx as ox
from creating_points import coordinate_point

from termcolor import colored

def get_subwaylines_of_bbox(bbox: tuple[float, float, float, float]) -> gpd.GeoDataFrame:
    tags = {"railway": ["subway", "light_rail"]}

    rail_lines = ox.features_from_bbox(bbox, tags=tags)

    if 'source' in rail_lines.columns:
        rail_lines = rail_lines[(rail_lines['source'] != 'Bing') & (rail_lines['source'].notna())]
    
   # Filter rail lines for line geometries only
    rail_lines = rail_lines[rail_lines.geometry.type.isin(["LineString", "MultiLineString"])]
    rail_lines = rail_lines.to_crs(epsg=3857)

    # Fixing Rail lines
    rail_lines = build_filtered_dataframe(rail_lines)
    rail_lines = connect_lines(rail_lines)

    return rail_lines

# if __name__ == "__main__":
#     bbox = (139.762, 35.6776, 139.8271, 35.7353)
#     subway_lines = get_subwaylines_of_bbox(bbox)
#     print(subway_lines)

from shapely.geometry import LineString

import osmnx as ox
from shapely.geometry import LineString, Point
import hashlib, os, logging, pickle

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


cache   = f"/home/honney/projects/gps-animation/cache"

def get_walking_line(start: coordinate_point, end: coordinate_point) -> LineString:
    """
    Returns a LineString of the shortest walking route between (lat, lon) points.
    Output is in EPSG:3857 (Web Mercator).
    """
    print(colored("Getting walking line from ", 'green') + colored(f"{start.get_name()} to {end.get_name()}", 'blue'))
    start = start.coord()
    end = end.coord()

    def create_cache_key(start_point, end_point):
        # Create a unique key from the coordinates
        coords_str = f"{start_point[0]}_{start_point[1]}_{end_point[0]}_{end_point[1]}"
        return hashlib.md5(coords_str.encode('utf-8')).hexdigest()
    
    cache_key = create_cache_key(start, end)
    cache_file = os.path.join(cache, f"walking_route_{cache_key}.pkl")

    # Check if cached result exists
    if os.path.exists(cache_file):
        try:
            with open(cache_file, 'rb') as f:  # Note: 'rb' for binary read
                cached_result = pickle.load(f)
                print(colored(f"Loading cached walking line from {cache_file}", 'yellow'))
                return cached_result
        except (pickle.PickleError, EOFError, FileNotFoundError, UnicodeDecodeError) as e:
            # If cache is corrupted or unreadable, continue to compute normally
            print(colored(f"Cache file {cache_file} is corrupted or unreadable: {e}. Recomputing...", 'red'))
            try:
                os.remove(cache_file)  # Remove corrupted file
                print(colored(f"Removed corrupted cache file: {cache_file}", 'yellow'))
            except:
                pass

    # Build graph in WGS84 (lat, lon required here!)
    G = ox.graph_from_point(
        (start[0], start[1]),  # (lat, lon)
        dist=5000,
        network_type="walk"
    )

    # Project to EPSG:3857
    G_proj = ox.project_graph(G, to_crs="EPSG:3857")

    # Project input points to EPSG:3857
    start_proj = ox.projection.project_geometry(
        Point(start[1], start[0]), crs="EPSG:4326", to_crs="EPSG:3857"
    )[0]
    end_proj = ox.projection.project_geometry(
        Point(end[1], end[0]), crs="EPSG:4326", to_crs="EPSG:3857"
    )[0]

    # Find nearest nodes in projected graph
    start_node = ox.distance.nearest_nodes(G_proj, start_proj.x, start_proj.y)
    end_node = ox.distance.nearest_nodes(G_proj, end_proj.x, end_proj.y)

    # Compute shortest path
    route = ox.shortest_path(G_proj, start_node, end_node, weight="length")
    if route is None:
        raise ValueError(colored("No walking route found between start and end points.", 'red'))

    # Build LineString in EPSG:3857
    route_coords = [(G_proj.nodes[node]['x'], G_proj.nodes[node]['y']) for node in route]

    line_string = LineString(route_coords)

    # Cache the result
    try:
        os.makedirs(cache, exist_ok=True)  # Create cache directory if it doesn't exist
        with open(cache_file, 'wb') as f:
            pickle.dump(line_string, f)
        print(colored(f"Cached walking line to {cache_file}", 'green'))
    except Exception as e:
        print(colored(f"Failed to cache result: {e}", 'red'))
    return line_string



# if __name__ == "__main__":
#     # point1 = coordinate_point(35.6936148, 139.7824489, "Comfort Hotel Tokyo Higashi Nihonbashi", "13:55", "13:57", None)
#     # point2 = coordinate_point(35.6943669, 139.7854539, "Higashi-Nihombashi Station", "13:58", "15:25", None)
#     # point1 = coordinate_point(35.708766,139.795991, "Asakusa Sta.", "13:55", "13:57", None)
#     # point2 = coordinate_point(35.714722, 139.79675, "Asakusa-Schrein", "13:58", "15:25", None)
#     # point1 = coordinate_point(35.714722, 139.79675, "Asakusa-Schrein", "13:58", "15:25", None)
#     # point2 = coordinate_point(35.713844, 139.793440, "Sushirō: Tokyo Rakutenchi Asakusa Building", "13:55", "13:57", None)
#     # point1 = coordinate_point(35.713844, 139.793440, "Sushirō: Tokyo Rakutenchi Asakusa Building", "13:55", "13:57", None)
#     # point2 = coordinate_point(35.712359, 139.788509, "Hashitou", "13:58", "15:25", None)
#     point1 = coordinate_point(35.712359, 139.788509, "Hashitou", "13:58", "15:25", None)
#     point2 = coordinate_point(35.719849, 139.783981, "Iriya Sta.", "13:55", "13:57", None)
#     route = get_walking_line(point1, point2)
#     print(f"Walking route from {point1.name} to {point2.name}: {route}")
#     bbox = [139.762, 35.6776, 139.8271, 35.7353]
#     from creating_maps import draw_path_on_map
#     # print(route)
#     draw_path_on_map(
#         image_path='/home/honney/projects/gps-animation/output/detail.png',
#         bbox_wgs84=bbox,
#         linestring_mercators=[route],
#         output_path='/home/honney/projects/gps-animation/output/path_plot_with_line_1.png',
#         colors=['blue'],  # Assuming walking lines are blue,
#         thickness=1
#     )


def get_part_of_line(geometry: LineString, start: list[float, float], end: list[float, float], debug = 0) -> LineString:
    has_started = 0
    has_ended = 0
    new_geometry = []
    for point in geometry.coords:
        if has_started == 1 or has_ended == 1:
            new_geometry.append(point)
        if point[0] == start[0] and point[1] == start[1]:
            if has_ended == 1:
                return LineString(new_geometry[:-1])
            else:
                has_started = 1
        if point[0] == end[0] and point[1] == end[1]:
            new_geometry.append(point)
            if debug == 1:
                print(colored(f"get_part_of_line: Returning segment from {start} to {end}: ", 'green'), colored(f"{new_geometry}", 'blue'))
            else:
                print(colored(f"get_part_of_line: Returning segment from {start} to {end}", 'green'))

            if has_started == 1:
                return LineString(new_geometry)
            else:
                has_ended = 1
            if has_started == 1 and has_ended == 1:
                raise ValueError(colored("Something Broke... It did not end despite that it should have.", 'red'))
    raise ValueError(colored("LineString does not contain the specified start and end points.", 'red'))

import math

def get_train_line(start: coordinate_point, end: coordinate_point, subway_map: gpd.GeoDataFrame, debug = 0) -> LineString:
    # Create a GeoDataFrame for the train line
    print(colored("Getting train line from ", 'green') + colored(f"{start.get_name()} to {end.get_name()}", 'blue'))
    # print(f"Subway map: {subway_map}")
    geometries = subway_map.geometry
    start_coords = start.get_mercator_coordinates()
    end_coords = end.get_mercator_coordinates()
    min_geometry_distance = []
    for geometry in geometries:
        min_distance_start = np.inf
        min_distance_end = np.inf
        for point in geometry.coords:
            distance_start = math.sqrt((start_coords[0] - point[0]) ** 2 + (start_coords[1] - point[1]) ** 2)
            distance_end = math.sqrt((end_coords[0] - point[0]) ** 2 + (end_coords[1] - point[1]) ** 2)
            if distance_start < distance_end:
                if distance_start < min_distance_start:
                    min_distance_start = distance_start
            else:
                if distance_end < min_distance_end:
                    min_distance_end = distance_end
        min_geometry_distance.append((min_distance_start, min_distance_end))
    # print(f"Minimum distances for each geometry: {min_geometry_distance}")
    min_distances = []
    min_distance = np.inf
    min_idx = -1
    for geometry_distance in min_geometry_distance:
        if geometry_distance[0]+geometry_distance[1] < min_distance:
            min_distance = geometry_distance[0]+geometry_distance[1]
            min_distances = geometry_distance
            min_idx = min_geometry_distance.index(geometry_distance)
    if min_idx != -1:
        name = subway_map.iloc[min_idx]['name:en']
        if debug == 1:
            print(colored(f"Found closest geometry: {name} with distances ", 'green'), colored(f"{min_distances}", 'blue'))
    correct_geometry = subway_map.iloc[min_idx]['geometry']
    correct_color = subway_map.iloc[min_idx]['colour']
    correct_start = None
    correct_end = None
    for point in correct_geometry.coords:
        distance_start = math.sqrt((start_coords[0] - point[0]) ** 2 + (start_coords[1] - point[1]) ** 2)
        distance_end = math.sqrt((end_coords[0] - point[0]) ** 2 + (end_coords[1] - point[1]) ** 2)
        if distance_start == min_distances[0]:
            correct_start = point
        elif distance_end == min_distances[1]:
            correct_end = point
    
    cut_geometry = get_part_of_line(correct_geometry, correct_start, correct_end)
    # print(f"Correct geometry: {type(correct_geometry)}")
    # print(f"Cut geometry: {cut_geometry}")
    # if cut_geometry == None:
    #     cut_geometry = get_part_of_line(LineString(list(correct_geometry)[-1]), correct_start, correct_end)
    # print(f"Cut geometry: {cut_geometry}")
    print(correct_color)
    return cut_geometry, correct_color

import numpy as np
# if __name__ == "__main__":
#     file = "/home/honney/projects/gps-animation/input/subway_map.geojson"
#     bbox = [np.float64(139.762), np.float64(35.6776), np.float64(139.8271), np.float64(35.7353)]
#     # subway_map = get_subwaylines_of_bbox(bbox)
#     # subway_map.to_file(file, driver='GeoJSON')
#     subway_map = gpd.read_file(file)
#     # point1 = coordinate_point(35.6992264, 139.785561, "Higashi-Nihombashi Station", None, None, None)
#     # point2 = coordinate_point(35.7103585, 139.8077607, "Oshiage Sta.(SKYTREE)", None, None, None)
#     # point1 = coordinate_point(35.7103585, 139.8077607, "Oshiage Sta.(SKYTREE)", None, None, None)
#     # point2 = coordinate_point(35.709006, 139.7944283, "Asakusa Sta.", None, None, None)
#     point1 = coordinate_point(35.7208778,139.7821198, "Iriya Sta.", None, None, None)
#     point2 = coordinate_point(35.692011,139.7782736, "Kodemmacho Sta.", "18:20", "18:30", None)
#     geometry = get_train_line(point1, point2, subway_map)
#     from creating_maps import draw_path_on_map
#     draw_path_on_map(
#         image_path='/home/honney/projects/gps-animation/output/detail.png',
#         bbox_wgs84=bbox,
#         linestring_mercators=[geometry],
#         output_path='/home/honney/projects/gps-animation/output/path_plot_with_line.png',
#         colors=['red']  # Assuming train lines are red
#     )

def get_car_line(start: coordinate_point, end: coordinate_point, debug = 0) -> LineString:
    """
    Returns a LineString of the shortest driving route between (lat, lon) points.
    Output is in EPSG:3857 (Web Mercator).
    """
    start = start.coord()
    end = end.coord()
    print(colored("Getting car line from ", 'green') + colored(f"{start} to {end}", 'blue'))
    # Build graph in WGS84 (lat, lon required here!)
    G = ox.graph_from_point(
        (start[0], start[1]),  # (lat, lon)
        dist=5000,
        network_type="drive"   # 🚗 driving network instead of walking
    )

    # Project to EPSG:3857
    G_proj = ox.project_graph(G, to_crs="EPSG:3857")

    # Project input points to EPSG:3857
    start_proj = ox.projection.project_geometry(Point(start[1], start[0]), crs="EPSG:4326", to_crs="EPSG:3857")[0]
    end_proj = ox.projection.project_geometry(Point(end[1], end[0]), crs="EPSG:4326", to_crs="EPSG:3857")[0]

    # Find nearest nodes in projected graph
    start_node = ox.distance.nearest_nodes(G_proj, start_proj.x, start_proj.y)
    end_node = ox.distance.nearest_nodes(G_proj, end_proj.x, end_proj.y)

    # Compute shortest path
    route = ox.shortest_path(G_proj, start_node, end_node, weight="length")
    if route is None:
        raise ValueError("No driving route found between start and end points.")

    # Build LineString in EPSG:3857
    route_coords = [(G_proj.nodes[node]['x'], G_proj.nodes[node]['y']) for node in route]
    return LineString(route_coords)

# if __name__ == "__main__":
#     point1 = coordinate_point(35.7140705, 139.8026836, "Asakusa Sta.", "13:55", "13:57", None)
#     point2 = coordinate_point(35.714722, 139.79675, "Asakusa-Schrein", "13:58", "15:25", None)
#     route = get_car_line(point1.coord(), point2.coord())
#     print(f"Car route from {point1.name} to {point2.name}: {route}")
#     bbox = [139.762, 35.6776, 139.8271, 35.7353]
#     from creating_maps import draw_path_on_map
#     draw_path_on_map(
#         image_path='/home/honney/projects/gps-animation/output/detail.png',
#         bbox_wgs84=bbox,
#         linestring_mercator=route,
#         output_path='/home/honney/projects/gps-animation/output/path_plot_with_line_1.png'
#     )

def connect_two_lines(line1, line2):
    new_line = []
    for coord in line1.coords:
        new_line.append(coord)
    for coord in line2.coords:
        new_line.append(coord)
    return LineString(new_line)

def dist(point1, point2):
    # print(point1, point2)
    return np.sqrt((point1[0] - point2[0])**2 + (point1[1] - point2[1])**2)

def connect_line_arrays_simple(line_arrays: list[LineString]) -> LineString:
    """
    Connects multiple LineString arrays into a single LineString.
    """
    line = list(line_arrays[0].coords)
    for i in range(len(line_arrays)-1):
        line1 = list(line_arrays[i+1].coords)
        # line2 = list(line_arrays[i+1].coords)
        if dist(line[-1], line1[0]) < dist(line[-1], line1[-1]):
            if line[-1] == line1[0]:
                line1.remove(line1[0])
            line = line + line1
        else:
            if line[-1] == line1[-1]:
                line1.remove(line1[-1])
            line = line + line1[::-1]

    new_line = []
    old_coord = None
    for coord in line:
        # print(coord, old_coord)
        if coord != old_coord:
            # print("Appending coord")
            new_line.append(coord)
        old_coord = coord

    return LineString(new_line)
    # return combined_line

if __name__ == "__main__":
    # Example usage
    line1 = LineString([(0, 0), (1, 1)])
    line2 = LineString([(2, 2), (1, 1)])
    line3 = LineString([(2, 2), (3, 3)])
    
    combined_line = connect_line_arrays_simple([line1, line2, line3])
    print(f"Combined Line: {combined_line}")