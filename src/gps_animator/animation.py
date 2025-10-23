from manim import config
from pathlib import Path
from gps_animator.manim_app.scenes import PathOnMap
from gps_animator.manim_app.helpers import get_animation_details
from gps_animator.common.points import point_collection

def run_manim_scene(gps_points_file: Path, map_kind: str):
    points = point_collection()
    points.load_from_file(gps_points_file)
    bbox, background_image = get_animation_details(points, map_kind)

    scene = PathOnMap(points, bbox, background_image)
    scene.render()  # equivalent to CLI call

def main():
    print("Running Program A logic...")
    gps_points_file: Path = input("Please give the path to your points file:\n")
    map_kind: str = input("Which kind of Map do you want? (Satelite|Details)")
    run_manim_scene(gps_points_file, map_kind)


if __name__ == "__main__":
    main()
