import dataclasses
import shapely
import shapely.affinity


def diameter(geometry: shapely.geometry.base.BaseGeometry) -> float:
    coords = geometry.minimum_rotated_rectangle.exterior.coords
    corner0, corner1, corner2, _, _ = map(shapely.geometry.Point, coords)
    return max(corner0.distance(corner1), corner1.distance(corner2))


def chord_perpendicular_to_point(polygon: shapely.Polygon,
                                 point: shapely.Point) -> shapely.LineString:
    # line from the centroid to the point
    toward = shapely.LineString([polygon.centroid, point])
    # line from the centroid directly away from the point
    away = shapely.affinity.rotate(toward, angle=180, origin=polygon.centroid)
    # combine the two lines
    line = shapely.MultiLineString([toward, away])
    line = shapely.simplify(shapely.line_merge(line), tolerance=0)
    # rotate the line to be perpendicular
    line = shapely.affinity.rotate(line, angle=90, origin=polygon.centroid)
    # return only the portion of the line that intersects the polygon
    # (using the convex hull here to guarantee only 2 intersections)
    return line.intersection(polygon.convex_hull)


@dataclasses.dataclass
class GeoCardinal:
    azimuth: int

    def of(self,
           polygon: shapely.Polygon,
           distance: float = 0) -> shapely.Polygon:
        length = distance + diameter(polygon)
        y = polygon.centroid.y + length
        # line at azimuth 0 (i.e., North)
        line = shapely.LineString([polygon.centroid, (polygon.centroid.x, y)])
        # rotate line to specified azimuth (negative = clockwise)
        line = shapely.affinity.rotate(line, -self.azimuth, origin=polygon.centroid)
        # collect points along the arc
        coordinates = [polygon.centroid]
        for angle in range(-45, +45 + 1, 15):
            rotated_line = shapely.affinity.rotate(
                line, -angle, origin=polygon.centroid)
            _, coordinate = rotated_line.coords
            coordinates.append(coordinate)
        # add the centroid again and construct the polygon
        coordinates.append(polygon.centroid)
        result = shapely.Polygon(coordinates)
        # if a distance is provided, remove the region nearest to the polygon
        if distance:
            result -= polygon.centroid.buffer(distance)
        # keep only the region that does not overlap with the input
        return result - polygon


North = GeoCardinal(azimuth=0)
NorthEast = GeoCardinal(azimuth=45)
East = GeoCardinal(azimuth=90)
SouthEast = GeoCardinal(azimuth=135)
South = GeoCardinal(azimuth=180)
SouthWest = GeoCardinal(azimuth=225)
West = GeoCardinal(azimuth=270)
NorthWest = GeoCardinal(azimuth=315)


class Near:
    @staticmethod
    def to(geometry: shapely.geometry.base.BaseGeometry, distance: float = 0):
        total_distance = distance + diameter(geometry)
        result = geometry.centroid.buffer(total_distance)
        if distance:
            result -= geometry.centroid.buffer(distance)
        return result - geometry


class GeoJsonReader:
    def __init__(self, root: str):
        self.root = root

    def read(self, osm) -> shapely.geometry.base.BaseGeometry:
        with open(f"{self.root}/{osm[:2]}/{osm}") as f:
            collection = shapely.from_geojson(f.read())
        [geometry] = collection.geoms
        # recover polygons that were inappropriately stored as MultiLineStrings
        if isinstance(geometry, shapely.geometry.MultiLineString):
            parts = shapely.get_parts(geometry)
            polygons, cuts, dangles, invalid = shapely.polygonize_full(parts)
            if not cuts and not dangles and not invalid:
                geometry = shapely.multipolygons(shapely.get_parts(polygons))
        return geometry


# import shapely.plotting
# import matplotlib.pyplot as plt
# g = shapely.from_wkt("POLYGON ((1.05 1.0, 0.805 0.826, 0.805 1.274, 1.05 1.1, 1.0 1.1, 1.0 1.0, 1.05 1.0)))")
# shapely.plotting.plot_polygon(g)
# shapely.plotting.plot_points(g.centroid, color='black')
