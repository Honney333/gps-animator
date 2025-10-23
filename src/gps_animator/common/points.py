import math
import json
from gps_animator.common.utils import convert_time_to_seconds, convert_WGS84_Mercator

### Global Variables
time_format_code = "%H:%M"

class coordinate_point:
    name:       str
    latitude:   float
    longitude:  float
    arrival:    int|None
    departure:  int|None
    icon:       str|None
    icon_scale: str|None

    def __init__(self, lat: float, lon: float, name: str, arrival: str|None, departure: str|None, icon: str|None, icon_scale: float|None):
        self.latitude = lat
        self.longitude = lon
        self.name = name
        if arrival is None:
            self.arrival = 0
        elif type(arrival) is int:
            self.arrival = arrival
        elif type(arrival) is str:
            self.arrival = convert_time_to_seconds(arrival)
        else:
            self.arrival = arrival
        if departure is None:
            self.departure = 2**32
        elif type(departure) is int:
            self.departure = departure
        elif type(departure) is str:
            self.departure = convert_time_to_seconds(departure)
        else:
            self.departure = departure
        self.icon = icon
        self.icon_scale = icon_scale

    def coord(self):
        return (self.latitude, self.longitude)

    def get_name(self):
        return self.name
    
    def get_icon(self):
        return self.icon
    
    def get_icon_scale(self):
        return self.icon_scale
    
    def get_arrival(self):
        return self.arrival
    
    def get_departure(self):
        return self.departure

    def get_details(self):
        return (self.latitude, self.longitude, self.name, self.arrival, self.departure, self.icon, self.icon_scale)

    def get_icon(self):
        return self.icon

    def __str__(self):
        return f"Point {self.name} is at the coordinates: ({self.latitude}|{self.longitude}) and stay was from {self.arrival} to {self.departure}"

    def get_mercator_coordinates(self):
        return convert_WGS84_Mercator(self.latitude, self.longitude)

    def get_all_infos(self):
        return f"{self.latitude}; {self.longitude}; {self.name}; {self.arrival}; {self.departure}; {self.icon}; {self.icon_scale}"

class point_collection:
    points: list[coordinate_point, int] # list of points and their departure_types

    def __init__(self):
        self.points = []

    def add_point(self, point: coordinate_point, departure_type: int|str|None):
        if type(departure_type) is str:
            if departure_type.lower() == "end":
                departure_type = 0
            elif departure_type.lower() == "walking":
                departure_type = 1
            elif departure_type.lower() == "train":
                departure_type = 2
            elif departure_type.lower() == "car":
                departure_type = 3
            else:
                departure_type = 0
        elif departure_type is None:
            departure_type = 0
        elif type(departure_type) is int:
            if departure_type > 0 and departure_type <= 3:
                departure_type = departure_type
            else:
                departure_type = 0
        self.points.append((point, departure_type))

    def remove_point(self, point: coordinate_point):
        self.points.remove(point)

    def sort_points(self):
        self.points.sort(key=lambda p: (p[0].arrival if p[0].arrival is not None else 0))

    def get_points(self):
        self.sort_points()
        points = [point for point, _ in self.points]
        return points

    def get_point(self, name: str):
        for point, _ in self.points:
            if point.name == name:
                return point
        return None

    def get_point(self, time: int):
        for point, _ in self.points:
            if (point.arrival if point.arrival is not None else 0) <= time and (point.departure if point.departure is not None else float('inf')) >= time:
                return point
        return None
    
    def get_point(self, latitude: float, longitude: float):
        for point, _ in self.points:
            if point.latitude == latitude and point.longitude == longitude:
                return point
        return None

    def get_mercator_coordinates(self):
        self.sort_points()
        return [point.get_mercator_coordinates() for point in self.points]

    def get_all(self):
        self.sort_points()
        return self.points

    def get_point_data(self):
        array = []
        for point, _ in self.points:
            if point.icon is not None:
                array.append((point.latitude, point.longitude, point.name, point.icon))
            else:
                array.append((point.latitude, point.longitude, point.name))
        return array

    def get_minmax(self):
        
        min_lat = math.inf
        max_lat = -math.inf
        min_lon = math.inf
        max_lon = -math.inf

        for point in self.get_points():
            lat = point.latitude
            lon = point.longitude

            if lat < min_lat: min_lat = lat
            elif lat > max_lat: max_lat = lat
            if lon < min_lon: min_lon = lon
            elif lon > max_lon: max_lon = lon

        return min_lon, min_lat, max_lon, max_lat

    def __str__(self):
        string = ""
        for point, i in self.points:
            string += f"Point {point.name} is at the coordinates: ({point.latitude}|{point.longitude}) and stay was from {point.arrival} to {point.departure} and the departure Type is {i}\n"
        return string

    def save_as_file(self, file_path: str):
        data = []
        for point, dep_type in self.points:
            entry = {
                "name": point.name,
                "latitude": point.latitude,
                "longitude": point.longitude,
                "arrival": point.arrival,
                "departure": point.departure,
                "icon": point.icon,
                "icon_scale": point.icon_scale,   # ✅ added
                "dep_type": dep_type,
            }
            data.append(entry)

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)


    def load_from_file(self, file_path: str):
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        for entry in data:
            point = coordinate_point(
                float(entry["latitude"]),
                float(entry["longitude"]),
                entry["name"],
                entry["arrival"],
                entry["departure"],
                entry["icon"],
                entry.get("icon_scale"),   # ✅ safe loading (None if missing)
            )
            self.add_point(point, entry["dep_type"])
