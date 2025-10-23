from gps_animator.common.points import point_collection, coordinate_point

def read_data_from_csv(points: point_collection, file_path: str):
    import csv
    with open(file_path, newline='') as csvfile:
        reader = csv.DictReader(csvfile, delimiter=',', quotechar='"')
        print(reader.fieldnames)

        for row in reader:
            point = coordinate_point(
                lat = float(row['Latitude']),
                lon = float(row['Longitude']),
                name = row['Name'],
                arrival = int(row['Arrival_Time']) if row['Arrival_Time'] else None,
                departure = int(row['Departure_Time']) if row['Departure_Time'] else None,
                icon = row['Icon'] if row['Icon'] else None,
                icon_scale = float(row['Icon_Scale']) if row['Icon_Scale'] else None
            )
            points.add_point(
                point = point,
                departure_type= row['Departure_Type'] if row['Departure_Type'] else None
            )
    points.sort_points()
    return points

def main():
    points = point_collection()
    points = read_data_from_csv(points, '/home/honney/projects/gps-animation/input/points_table.csv')
    print(points)

if __name__ == "__main__":
    main()