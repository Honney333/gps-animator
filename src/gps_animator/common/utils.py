import time
from typing import Tuple
import pyproj
import numpy as np

time_format_code = "%H:%M"

def convert_time_to_seconds(time_str: str) -> int:
    t = time.strptime(time_str, time_format_code)
    return t.tm_hour * 3600 + t.tm_min * 60 + t.tm_sec

def convert_WGS84_Mercator(latitude: float, longitude: float) -> Tuple[float, float]:
        """
        Convert latitude/longitude (WGS84) to Web Mercator (EPSG:3857) coordinates
        
        Args:
            lat (float): Latitude in decimal degrees
            lon (float): Longitude in decimal degrees
        
        Returns:
            tuple: (x, y) coordinates in Web Mercator meters
        """
        # Define coordinate systems
        wgs84 = pyproj.CRS("EPSG:4326")  # WGS84 (standard lat/lon)
        mercator = pyproj.CRS("EPSG:3857")  # Web Mercator
        
        # Create transformer
        transformer = pyproj.Transformer.from_crs(wgs84, mercator, always_xy=True)
        
        # Convert coordinates
        x, y = transformer.transform(longitude, latitude)

        return x, y

def expand_bbox(bbox: tuple[float, float, float, float], expand_factor: float) -> tuple[float, float, float, float]:
    """Expand bbox by a given factor in all directions and return shapely box."""
    min_lon, min_lat, max_lon, max_lat = bbox
    lon_expand = (max_lon - min_lon) * expand_factor
    lat_expand = (max_lat - min_lat) * expand_factor
    return [
        np.round(min_lon - lon_expand, 4),
        np.round(min_lat - lat_expand, 4),
        np.round(max_lon + lon_expand, 4),
        np.round(max_lat + lat_expand, 4)
    ]