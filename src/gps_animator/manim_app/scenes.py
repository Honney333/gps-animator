from manim import *
import numpy as np
from shapely.geometry import LineString
from PIL import Image, ImageSequence
from termcolor import colored
import os
from gps_animator.manim_app.helpers import *
from gps_animator.common.points import point_collection

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


class PathOnMap(Scene):
    config.pixel_width = 3840
    config.pixel_height = 4046
    config.frame_rate = 60
    config.output_file = "/home/honney/projects/gps-animation/output/output_video.mp4"
    image_manim_width: float = 0
    image_manim_height: float = 0

    def __init__(self, baselayer_path: str, bbox: tuple[float, float, float, float], path: list[tuple[float, float]], **kwargs):
        super().__init__(**kwargs)
        self.baselayer_path = baselayer_path
        self.bbox = bbox
        self.path = path

    def add_base_path(self, path, color = WHITE, stroke_width=4):
        """
        Adds static base lines for reference.
        paths: list of tuples (start_point, end_point)
        color: color of the base lines
        """
        line = VMobject()
        line.set_points_smoothly(path)  # automatically smooths the corners
        line.set_stroke(color=color, width=stroke_width)
        line.set_z_index(1)
        self.add(line)
        return line
    
    def add_base_paths(self, paths, colors):
        """
        Adds static base lines for reference.
        paths: list of tuples (start_point, end_point)
        color: color of the base lines
        """
        for i in range(len(paths)):
            path = paths[i]
            color = colors[i]
            self.add_base_path(path, color=color)

    def show_media_at_point(self, point, media_path, show_time=2, scale=1, height=1):
        import numpy as np
        point = np.array(point, dtype=float)
        if point.shape[0] == 2:
            point = np.append(point, 0)

        ext = os.path.splitext(media_path)[1].lower()

        if ext in [".png", ".jpg", ".jpeg", ".bmp", ".webp"]:
            with Image.open(media_path) as img:
                width, _ = img.size
            obj = ImageMobject(media_path)

        elif ext == ".gif":
            gif = Image.open(media_path)
            print(gif.size)
            width, _ = gif.size
            frames = [ImageMobject(np.array(frame.convert("RGBA"))) for frame in ImageSequence.Iterator(gif)]
            frame_count = len(frames)
            frame_duration = gif.info.get("duration", 100) / 1000
            total_gif_time = frame_count * frame_duration

            obj = frames[0]

            def gif_updater(mob, dt):
                t = self.renderer.time
                idx = int((t % total_gif_time) / frame_duration) % frame_count
                old_center = mob.get_center()
                mob.become(frames[idx])
                mob.move_to(old_center)

            obj.add_updater(gif_updater)

        else:
            raise ValueError(f"Unsupported file type: {ext}")

        # --- Scale object to desired height ---
        obj.scale(rescale(scale, width))
        # print(f"Scaling: {rescale(scale, width)}")

        # --- Position it ---
        obj.move_to(point + UP * height * (obj.height / 2))
        obj.set_z_index(10)
        self.add(obj)
        self.wait(show_time)
        self.remove(obj)

    def move_image_along_path(
        self,
        points,
        media_path,
        show_time=1.5,
        scale=1,
        height=1
    ):
        """
        Moves an image/gif along a sequence of points.

        points: list of 2D points
        media_path: path to the media file
        duration_per_segment: time to move between each consecutive pair
        """
        ext = os.path.splitext(media_path)[1].lower()

        # --- Handle different media types ---
        if ext in [".png", ".jpg", ".jpeg", ".bmp", ".webp"]:
            with Image.open(media_path) as img:
                width, pixel_height = img.size
            obj = ImageMobject(media_path)

        elif ext == ".gif":
            gif = Image.open(media_path)
            width, _ = gif.size
            frames = [ImageMobject(np.array(frame.convert("RGBA"))) for frame in ImageSequence.Iterator(gif)]
            frame_count = len(frames)
            frame_duration = gif.info.get("duration", 100) / 1000
            total_gif_time = frame_count * frame_duration

            obj = frames[0]

            def gif_updater(mob, dt):
                t = self.renderer.time
                idx = int((t % total_gif_time) / frame_duration) % frame_count
                old_center = mob.get_center()
                mob.become(frames[idx])
                mob.move_to(old_center)

            obj.add_updater(gif_updater)

        else:
            raise ValueError(f"Unsupported file type: {ext}")

        # --- Scale object to desired height ---
        obj.scale(rescale(scale, width))
        # print(f"Scaling: {rescale(scale, width)}")

        # --- Place initial position ---
        obj.set_z_index(10)
        obj.move_to(points[0] + height * UP * (obj.height / 2))
        self.add(obj)

        # --- Animate along path ---
        for start, end in zip(points[:-1], points[1:]):
            line = Line(start, end)
            tracker = ValueTracker(0)

            def update_obj(mob):
                pos = line.point_from_proportion(tracker.get_value())
                if height == 1:
                    mob.move_to(pos + UP * (mob.height / 2))
                else:
                    mob.move_to(pos)

            obj.add_updater(update_obj)

            self.play(
                tracker.animate.set_value(1),
                run_time=show_time,
                rate_func=linear,
            )

            obj.remove_updater(update_obj)
            obj.move_to(end + UP * (obj.height / 2))

        # --- Remove at the end ---
        self.remove(obj)

    def move_image_along_paths(self, paths, transport, times):
        # i=0
        for path, travel, time in zip(paths, transport, times):
            # i+=1
            # if i == 1:
            #     continue
            # if i == 3:
            #     return
            print(colored(f"animating path from {list(path[0])} to {list(path[-1])}, which used {travel} and was from {time[0]} to {time[-1]}", 'red'))
            # print(path, travel, time1, time2)
            point1 = path[0]
            # Calculate overall distance of path
            overall_distance = 0
            for point2 in path[1:]:
                if point2[0] == path[-1][0] and point2[1] == path[-1][1]:
                    continue
                overall_distance += distance(point1, point2)
                point1 = point2
            # Calculated overall distance of path
            overall_duration = time[1] - time[0]
            if overall_duration > MAX_TRAVEL:
                overall_duration = MAX_TRAVEL
            point1 = path[0]
            last_point = []
            if travel == "walking":
                buffer = 5
            else:
                buffer = 1
            for point2 in path[1:]:
                if len(last_point) > buffer:
                    last_point.pop(0)
                dist_points = distance(point1, point2)
                segment_duration = (dist_points / overall_distance) * overall_duration
                # print(f"normal animation: {segment_duration}")
                if (segment_duration <= 0.5 and travel == "walking") or (segment_duration <= 0.15 and (travel == "train" or travel == "car")) and (point2 != path[-1]).any():
                    continue
                if segment_duration == 0:
                    segment_duration = 0.016666667
                last_angle=[angle_between_two_points_2d(point1, point2)]
                if len(last_point) > 0:
                    for point in last_point:
                        angle = angle_between_two_points_2d(point, point2)
                        last_angle.append(angle)
                angle = np.mean(np.array(last_angle))
                if travel == "walking":
                    possible_angles = [0, 90, 180, 270]
                    img_home_path = f"{assets}/walking/{find_nearest(possible_angles, angle)}.gif"
                    # print(f"animation: {img_home_path}")
                    self.move_image_along_path([point1, point2], img_home_path, show_time=segment_duration, scale=0.9, height=0.5)
                elif travel == "train":
                    possible_angles = [0.0, 5.625, 11.25, 16.875, 22.5, 28.125, 33.75, 39.375, 45.0, 50.625, 56.25, 61.875, 67.5, 73.125, 78.75, 84.375, 90.0, 95.625, 101.25, 106.875, 112.5, 118.125, 123.75, 129.375, 135.0, 140.625, 146.25, 151.875, 157.5, 163.125, 168.75, 174.375, 180.0, 185.625, 191.25, 196.875, 202.5, 208.125, 213.75, 219.375, 225.0, 230.625, 236.25, 241.875, 247.5, 253.125, 258.75, 264.375, 270.0, 275.625, 281.25, 286.875, 292.5, 298.125, 303.75, 309.375, 315.0, 320.625, 326.25, 331.875, 337.5, 343.125, 348.75, 354.375]
                    img_home_path = f"{assets}/subway/{find_nearest(possible_angles, angle)}.png"
                    self.move_image_along_path([point1, point2], img_home_path, show_time=segment_duration, scale = 1.2, height=0)
                elif travel == "car":
                    possible_angles = [0.0, 5.625, 11.25, 16.875, 22.5, 28.125, 33.75, 39.375, 45.0, 50.625, 56.25, 61.875, 67.5, 73.125, 78.75, 84.375, 90.0, 95.625, 101.25, 106.875, 112.5, 118.125, 123.75, 129.375, 135.0, 140.625, 146.25, 151.875, 157.5, 163.125, 168.75, 174.375, 180.0, 185.625, 191.25, 196.875, 202.5, 208.125, 213.75, 219.375, 225.0, 230.625, 236.25, 241.875, 247.5, 253.125, 258.75, 264.375, 270.0, 275.625, 281.25, 286.875, 292.5, 298.125, 303.75, 309.375, 315.0, 320.625, 326.25, 331.875, 337.5, 343.125, 348.75, 354.375]
                    img_home_path = f"{assets}/car/{find_nearest(possible_angles, angle)}.png"
                    self.move_image_along_path([point1, point2], img_home_path, show_time=segment_duration, scale = 1, height=0)
                point1 = point2
                last_point.append(point2)
            if len(time) == 3:
                img_home_path = f"{assets}/idle/idle.gif"
                segment_duration = min(time[2]-time[1], 10)
                # print(f"idle time: {segment_duration}, animation: {img_home_path}")
                # print(path[-1], type(path[-1]), type(path[-1][0]))
                if segment_duration > MIN_IDLE:
                    self.show_media_at_point(path[-1], img_home_path, show_time=IDLE_TIME, scale = 1, height=1)
            # return

    def put_background_image(self, image_path, bbox):
        """Adds a background image to the scene."""
        min_lon, min_lat, max_lon, max_lat = bbox
        minx, miny = lonlat_to_mercator(min_lon, min_lat)
        maxx, maxy = lonlat_to_mercator(max_lon, max_lat)

        # Make sure bbox extents are positive
        if maxx <= minx or maxy <= miny:
            raise ValueError("Converted Mercator bbox has non-positive extent")

        merc_width = maxx - minx
        merc_height = maxy - miny
        image_manim_width = IMAGE_MANIM_WIDTH
        image_manim_height = image_manim_width * (merc_height / merc_width)
        px_w = 3840
        px_h = max(10, int(px_w * (merc_height / merc_width)))
        self.minx = minx
        self.miny = miny
        self.maxx = maxx
        self.maxy = maxy
        self.merc_width = merc_width
        self.merc_height = merc_height
        self.image_manim_width = image_manim_width
        self.image_manim_height = image_manim_height
        print(f"Image size: {px_w} x {px_h}")

        # Open your image and resize it to match resolution
        img = Image.open(image_path)
        img = img.resize((px_w, px_h), Image.LANCZOS)

        # Save to a temporary file for Manim
        resized_path = "resized_map.png"
        img.save(resized_path)

        # Load the resized image as an ImageMobject
        map_img = ImageMobject(resized_path)
        map_img.width = image_manim_width
        map_img.height = image_manim_height
        map_img.move_to(ORIGIN)

        # Add image and keep it always in the background
        self.add(map_img)
        self.bring_to_back(map_img)

    def add_media_at_point(self, point, media_path, scale=1, height=1, z_index=2):
        """
        Adds an image, GIF, or video at a fixed position for the entire animation.
        point: (x, y) or (x, y, z)
        media_path: path to the media file
        scale: overall scaling factor
        height: relative height offset
        z_index: layering order
        """
        point = np.array(point, dtype=float)
        if point.shape[0] == 2:
            point = np.append(point, 0)

        ext = os.path.splitext(media_path)[1].lower()

        if ext in [".png", ".jpg", ".jpeg", ".bmp", ".webp"]:
            obj = ImageMobject(media_path)
            with Image.open(media_path) as img:
                width, _ = img.size

        elif ext == ".gif":
            gif = Image.open(media_path)
            width, _ = gif.size
            frames = [ImageMobject(np.array(frame.convert("RGBA"))) for frame in ImageSequence.Iterator(gif)]
            frame_count = len(frames)
            frame_duration = gif.info.get("duration", 100) / 1000
            total_gif_time = frame_count * frame_duration

            obj = frames[0]

            def gif_updater(mob, dt):
                t = self.renderer.time
                idx = int((t % total_gif_time) / frame_duration) % frame_count
                old_center = mob.get_center()
                mob.become(frames[idx])
                mob.move_to(old_center)

            obj.add_updater(gif_updater)

        else:
            raise ValueError(f"Unsupported file type: {ext}")

        # --- Scale object to desired height ---
        obj.scale(rescale(scale, width))
        # print(f"Scaling: {rescale(scale, width)}")

        # --- Position it ---
        obj.move_to(point + UP * height * (obj.height / 2))
        obj.set_z_index(z_index)

        # --- Add to scene permanently ---
        self.add(obj)

    def construct(self):
        points = point_collection()
        points.load_from_file(f"{input}/points.txt")
        
        all_points = points.get_points()
        bbox = points.get_minmax()
        extra_scale = .5
        dpi = 600
        from creating_maps import expand_bbox
        bbox_scaled = expand_bbox(bbox, extra_scale)

        image_path = '/home/honney/projects/gps-animation/output/detail.png'

        self.put_background_image(image_path = image_path, bbox = bbox_scaled)

        # Conversion from Mercator meters -> Manim coordinates (centered)
        def merc_to_manim(x, y):
            fx = (x - self.minx) / self.merc_width
            fy = (y - self.miny) / self.merc_height
            mx = fx * self.image_manim_width - self.image_manim_width / 2.0
            my = fy * self.image_manim_height - self.image_manim_height / 2.0
            return np.array([mx, my, 0.0])

        for point in all_points:
            icon = point.get_icon()
            icon_scale = point.get_icon_scale()
            # print(f"\"{icon}\" with type: {type(icon)}")
            if icon != None:
                x, y = point.get_mercator_coordinates()
                self.add_media_at_point(merc_to_manim(x, y), icon, scale=1.5*icon_scale, height=0.5)
        line_parts, times, colors, transport = get_path_array(points, bbox_scaled)

        times = get_appropriate_times(times, 600)

        new_line_parts = []
        for line in line_parts:
            new_line_parts.append([merc_to_manim(x,y) for x,y in line.coords])
        
        paths = resort_path(new_line_parts)
        
        self.add_base_paths(paths, colors)

        self.move_image_along_paths(paths, transport, times)