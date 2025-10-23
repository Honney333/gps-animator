from termcolor import colored
from pathlib import Path
import os
from gps_animator.common.points import point_collection, coordinate_point
from gps_animator.common.utils import expand_bbox, convert_WGS84_Mercator
from gps_animator.config import settings
from gps_animator.common.map_utils import save_osm_detail_map, save_satellite_map

### Global Variables
end     = 0
walking = 1
train   = 2
car     = 3
assets  = f"/home/honney/projects/gps-animation/assets"
input   = f"/home/honney/projects/gps-animation/input"
output  = f"/home/honney/projects/gps-animation/output"
cache   = f"/home/honney/projects/gps-animation/cache"
debug   = 0
MIN_IDLE = 5 
IDLE_TIME = 2.5
MAX_TRAVEL = 10
IMAGE_MANIM_WIDTH = 12.0

def get_animation_details(points: point_collection, map_kind: str, bbox_scale: float = 0.5, image_cache: Path = settings.INPUT) -> tuple[tuple[float, float, float, float], Path, int, int]:
    bbox = expand_bbox(points.get_minmax(), bbox_scale)
    min_lon, min_lat, max_lon, max_lat = bbox
    minx, miny = convert_WGS84_Mercator(min_lat, min_lon)
    maxx, maxy = convert_WGS84_Mercator(max_lat, max_lon)
    if maxx <= minx or maxy <= miny:
        raise ValueError("Converted Mercator bbox has non-positive extent")
    merc_width = maxx - minx
    merc_height = maxy - miny
    animation_width = IMAGE_MANIM_WIDTH
    animation_height = animation_width * (merc_height / merc_width)

    if map_kind == "Satelite":
        map_path = save_satellite_map(bbox = bbox, filename = os.path.join(image_cache, "satelite.png"))
    elif map_kind == "Details":
        map_path = save_osm_detail_map(bbox = bbox, filename = os.path.join(image_cache, "detail.png"))
    else:
        raise ValueError(f"Map kind: {map_kind} is not a valid option")

    return bbox, map_path, animation_width, animation_height

def get_path_array(points, bbox_scaled):
    line_parts=[] # array of LineString, colors
    times = []
    colors = []
    transport = []

    from gps_animator.common.build_line import get_subwaylines_of_bbox
    subway_map = get_subwaylines_of_bbox(bbox_scaled)
    point_table = points.get_all()
    
    from gps_animator.common.build_line import get_walking_line, get_train_line, get_car_line
    for i in range(len(point_table)-1):
        try:
            print()
            point = point_table[i][0]
            next_point = point_table[i+1][0]
            # print(colored(f"Processing line from\n{point.get_name()} to\n{next_point.get_name()}", 'black'))
            if point_table[i][1] == end:
                break
            elif point_table[i][1] == walking:
                line_parts.append(get_walking_line(point, next_point))
                colors.append("#583927")
                times.append((point.get_departure(), next_point.get_arrival()))
                transport.append("walking")
                # pass
            elif point_table[i][1] == train:
                line_part, color = get_train_line(point, next_point, subway_map)
                if debug == 1:
                    print(line_part, color)
                line_parts.append(line_part)
                colors.append(color)
                times.append((point.get_departure(), next_point.get_arrival()))
                transport.append("train")
            elif point_table[i][1] == car:
                line_parts.append(get_car_line(point, next_point))
                colors.append("#808080")
                times.append((point.get_departure(), next_point.get_arrival()))
                transport.append("car")
            else:
                raise ValueError(f"Unknown point type: {point_table[i][1]}")
        except Exception as e:
            print(colored(f"Error processing line from {point.get_name()} to {next_point.get_name()}: {e}", 'red'))
            print(colored(f"{point_table[i][1]}", 'yellow'))
            continue
    print()
    return line_parts, times, colors, transport

def lonlat_to_mercator(lon, lat):
    """Convert lon/lat in degrees to Web Mercator (EPSG:3857) meters.
    Uses the spherical Mercator formulas (same as pyproj/GDAL usually).
    """
    R = 6378137.0
    x = R * np.radians(lon)
    # clamp latitude to valid range to avoid infinities
    lat = np.clip(lat, -85.05112878, 85.05112878)
    y = R * np.log(np.tan(np.pi / 4.0 + np.radians(lat) / 2.0))
    return float(x), float(y)

def get_appropriate_times(times, total_duration, min_faktor = 0.1, pause_multiplier = 0.1):
    # Adjust times to fit within the total duration
    time_array = []
    for arrival, departure in times:
        if not arrival == None:
            time_array.append(arrival)
        if not departure == None:
            time_array.append(departure)
    begin_time = time_array[0]
    time_array = [time - begin_time for time in time_array]
    total_time = time_array[-1] - time_array[0]
    time_array = [ (t / total_time) * total_duration for t in time_array]
    final_time_array = []
    for i in range(len(time_array)//2):
        # print(i, len(time_array)//2, len(time_array))
        if i < (len(time_array)//2)-1 and time_array[i*2+2]-time_array[i*2+1] >= total_duration * min_faktor:
            final_time_array.append([time_array[i*2], time_array[i*2+1], time_array[i*2+1] + pause_multiplier * (time_array[i*2+2]-time_array[i*2+1])])
        else:
            final_time_array.append([time_array[i*2], time_array[i*2+1]])
    return final_time_array

def distance(point1, point2):
    """Calculates the distance between two points."""
    return np.linalg.norm(np.array(point1) - np.array(point2))

def fix_paths_direction(paths):
    """Ensures the path is directed from start to end."""
    last_path = None
    new_paths = []
    for i in range(len(paths)):
        path = paths[i]
        if last_path is not None:
            if distance(path[0], last_path[-1]) > distance(path[-1], last_path[-1]):
                path = path[::-1]  # reverse path

            if path[0] != last_path[-1]:
                path = [last_path[-1]] + path
        last_path = path
        new_paths.append(path)
    return new_paths

import numpy as np

def angle_between_two_points_2d(point1, point2):
    """Calculates the angle between two points in degrees.
    0° = up (positive y), 90° = right (positive x), 
    180° = down (negative y), 270° = left (negative x).
    """
    delta_x = point2[0] - point1[0]
    delta_y = point2[1] - point1[1]
    
    # Compute atan2 with swapped axes (to make y+ = 0°)
    angle = np.degrees(np.arctan2(delta_x, delta_y))
    
    # Ensure result is in [0, 360)
    angle = (angle + 360) % 360
    return angle

# print(angle_between_two_points_2d((0, 0), (1, 0))) = 0.0
# print(angle_between_two_points_2d((0, 0), (1, 1))) = 45.0
# print(angle_between_two_points_2d((0, 0), (-1, 1))) = 135.0

def find_nearest(array, value):
    array = np.asarray(array)
    idx = (np.abs(array - value)).argmin()
    return array[idx]

# possible_angles = [0.0, 90, 180, 270]
# angle = angle_between_two_points_2d((0, 0), (3, -1))
# print(angle, find_nearest(possible_angles, angle))

def rescale(scale_factor, resolution, standard_resolution=64):
    # print(f"Scale factor: {scale_factor}, Resolution: {resolution}, Standard Resolution: {standard_resolution}")
    return np.multiply(np.divide(standard_resolution, resolution), scale_factor)

# rescale(1.5, 128)

def resort_path(paths):
    last_path = None
    new_paths = []
    for i in range(len(paths)):
        path = paths[i]
        if last_path is not None:
            if distance(path[0], last_path[-1]) > distance(path[-1], last_path[-1]):
                path = path[::-1]  # reverse path
            if (path[0] != last_path[-1]).any():
                path = [last_path[-1]] + path
        last_path = path
        new_paths.append(path)
    return new_paths