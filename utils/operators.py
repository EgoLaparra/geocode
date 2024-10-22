import dataclasses
import shapely
import shapely.affinity
import geopandas
import matplotlib.pyplot as plt


def show_plot(*geometries: shapely.geometry.base.BaseGeometry):
    gdf = geopandas.GeoDataFrame(geometry=list(geometries), crs='EPSG:4326')
    gdf.plot(color=plt.rcParams['axes.prop_cycle'].by_key()['color'], aspect='equal')
    plt.show()


def diameter(geometry: shapely.geometry.base.BaseGeometry):
    coords = geometry.minimum_rotated_rectangle.exterior.coords
    corner0, corner1, corner2, _, _ = map(shapely.geometry.Point, coords)
    return max(corner0.distance(corner1), corner1.distance(corner2))


def _diameter_and_start(geometry: shapely.geometry.base.BaseGeometry,
                        distance: float = None) -> (float, float):
    d = diameter(geometry)
    radius = d / 2
    if distance is None:
        start_distance = radius
    else:
        start_distance = max(0.0, distance - radius)
    return d, start_distance


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
           geometry: shapely.geometry.base.BaseGeometry,
           distance: float = None) -> shapely.Polygon:
        d, start_distance = _diameter_and_start(geometry, distance)
        # line at azimuth 0 (i.e., North)
        y = geometry.centroid.y + start_distance + d
        line = shapely.LineString([geometry.centroid, (geometry.centroid.x, y)])
        # rotate line to specified azimuth (negative = clockwise)
        line = shapely.affinity.rotate(line, -self.azimuth, origin=geometry.centroid)
        # collect points along the arc
        coordinates = [geometry.centroid]
        for angle in range(-45, +45 + 1, 15):
            rotated_line = shapely.affinity.rotate(
                line, -angle, origin=geometry.centroid)
            _, coordinate = rotated_line.coords
            coordinates.append(coordinate)
        # add the centroid again and construct the polygon
        coordinates.append(geometry.centroid)
        result = shapely.Polygon(coordinates)
        # if a distance is provided, remove the region nearest to the input
        if distance is not None and start_distance > 0:
            result -= geometry.centroid.buffer(start_distance)
        # keep only the region that does not overlap with the input
        return result - geometry


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
    def to(geometry: shapely.geometry.base.BaseGeometry,
           distance: float = None):
        d, start_distance = _diameter_and_start(geometry, distance)
        result = geometry.centroid.buffer(start_distance + d)
        if distance is not None and start_distance > 0:
            result -= geometry.centroid.buffer(start_distance)
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
