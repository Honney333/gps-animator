from gps_animator.common.points import point_collection, coordinate_point

def example_build_save(path: str):
    end     = 0
    walking = 1
    train   = 2
    car     = 3
    assets  = f"/home/honney/projects/gps-animation/assets"
    output  = f"/home/honney/projects/gps-animation/output"

    print("Creating point collection")
    point_collection1 = point_collection()
    point_collection1.add_point(coordinate_point(35.6936148, 139.7824489, "Comfort Hotel Tokyo Higashi Nihonbashi", None, "09:58", f"{assets}/points/hotel.png", 0.75), walking)
    point_collection1.add_point(coordinate_point(35.6943669, 139.7854539, "Higashi-Nihombashi Station", "10:15", "10:36", None, None), train)
    point_collection1.add_point(coordinate_point(35.7104707, 139.8108069, "SKYTREE", "10:42", "13:52", f"{assets}/points/skytree.png", 1), train)
    point_collection1.add_point(coordinate_point(35.708766, 139.795991, "Asakusa Sta.", "13:55", "13:57", None, None), walking)
    point_collection1.add_point(coordinate_point(35.714722, 139.79675, "Asakusa-Schrein", "13:58", "15:25", f"{assets}/points/asakusa.png", 1), walking)
    point_collection1.add_point(coordinate_point(35.713844, 139.793440, "Sushirō: Tokyo Rakutenchi Asakusa Building", "15:27", "16:49", f"{assets}/points/sushi.png", 0.5), walking)
    point_collection1.add_point(coordinate_point(35.712359, 139.788509, "Hashitou", "16:54", "17:42", f"{assets}/points/stabchen.png", 0.5), walking)
    point_collection1.add_point(coordinate_point(35.719849, 139.783981, "Iriya Sta.", "17:54", "18:12", None, None), train)
    point_collection1.add_point(coordinate_point(35.692011, 139.7782736, "Kodemmacho Sta.", "18:20", "18:30", None, None), walking)
    point_collection1.add_point(coordinate_point(35.6934191, 139.7835512, "Comfort Hotel Tokyo Higashi Nihonbashi", "18:42", None, None, None), None)
    print("All points added to collection")
    print("Saving points to file...")
    point_collection1.save_as_file(path)
    print("Points saved successfully")
    print(point_collection1)

def example_load(path: str):
    print("Loading points from file...")
    new_point_collection = point_collection()
    new_point_collection.load_from_file(path)
    print("Points loaded successfully")
    print(new_point_collection)
    # for point in new_point_collection.get_points():
    #     print(f"\"{point.get_icon()}\" with type: {type(point.get_icon())}")
    

if __name__ == "__main__":
    end     = 0
    walking = 1
    train   = 2
    car     = 3
    assets  = f"/home/honney/projects/gps-animation/assets"
    input   = f"/home/honney/projects/gps-animation/input"
    output  = f"/home/honney/projects/gps-animation/output"

    example_build_save(f"{input}/points.txt")
    example_load(f"{input}/points.txt")
    example_build_save(f"{output}/points.txt")
    example_load(f"{output}/points.txt")