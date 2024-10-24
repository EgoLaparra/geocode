import dataclasses
import shapely
import shapely.affinity
import geopandas
import matplotlib.pyplot as plt


def show_plot(*geometries: shapely.geometry.base.BaseGeometry):
    gdf = geopandas.GeoDataFrame(geometry=list(geometries), crs='EPSG:4326')
    color_list = plt.rcParams['axes.prop_cycle'].by_key()['color']
    gdf.plot(color=color_list, aspect='equal')
    plt.show()


def diameter(geometry: shapely.geometry.base.BaseGeometry):
    coords = geometry.minimum_rotated_rectangle.exterior.coords
    corner0, corner1, corner2, _, _ = map(shapely.geometry.Point, coords)
    return max(corner0.distance(corner1), corner1.distance(corner2))


@dataclasses.dataclass
class GeoCardinal:
    azimuth: int

    def of(self,
           geometry: shapely.geometry.base.BaseGeometry,
           distance: float = None) -> shapely.Polygon:
        centroid = geometry.centroid
        d, start_distance = _diameter_and_start(geometry, distance)
        # create point at azimuth 0 (North) and rotate (negative = clockwise)
        point = shapely.Point(centroid.x, centroid.y + start_distance + d)
        point = shapely.affinity.rotate(point, -self.azimuth, origin=centroid)
        # collect points along the arc
        arc = [shapely.affinity.rotate(point, -angle, origin=centroid)
               for angle in range(-45, +45 + 1, 15)]
        # add the centroid and construct the polygon
        result = shapely.Polygon([centroid] + arc + [centroid])
        # if a distance is provided, remove the region nearest to the input
        if distance is not None and start_distance > 0:
            result -= geometry.centroid.buffer(start_distance)
        # keep only the region that does not overlap with the input
        return result - geometry

    def part_of(self, geometry: shapely.geometry.base.BaseGeometry):
        d = diameter(geometry)
        c = geometry.centroid
        # create point at azimuth 0 (North) and rotate (negative = clockwise)
        point = shapely.Point(c.x, c.y + d)
        point = shapely.affinity.rotate(point, -self.azimuth, origin=c)
        # find a line perpendicular to that point
        line = _line_through_centroid_perpendicular_to_point(geometry, point)
        # find the one-directional buffer of the chord that crosses the point
        buf1 = line.buffer(distance=d, single_sided=True, cap_style='flat')
        buf2 = line.buffer(distance=-d, single_sided=True, cap_style='flat')
        polygon = buf1 if buf1.intersection(point) else buf2
        # keep only the region that overlaps with the input
        return polygon.intersection(geometry)


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


class Between:
    @staticmethod
    def of(geometry1: shapely.geometry.base.BaseGeometry,
           geometry2: shapely.geometry.base.BaseGeometry) -> shapely.Polygon:
        chord1 = _chord_perpendicular_to_point(geometry1, geometry2.centroid)
        chord2 = _chord_perpendicular_to_point(geometry2, geometry1.centroid)
        return chord1.union(chord2).convex_hull - geometry1 - geometry2


class GeoJsonDirReader:
    def __init__(self, root_dir: str):
        self.root_dir = root_dir

    def read(self, osm) -> shapely.geometry.base.BaseGeometry:
        with open(f"{self.root_dir}/{osm[:2]}/{osm}") as f:
            collection = shapely.from_geojson(f.read())
        [geometry] = collection.geoms
        # recover polygons that were inappropriately stored as MultiLineStrings
        if isinstance(geometry, shapely.geometry.MultiLineString):
            parts = shapely.get_parts(geometry)
            polygons, cuts, dangles, invalid = shapely.polygonize_full(parts)
            if not cuts and not dangles and not invalid:
                geometry = shapely.multipolygons(shapely.get_parts(polygons))
        return geometry


def _diameter_and_start(geometry: shapely.geometry.base.BaseGeometry,
                        distance: float = None) -> (float, float):
    d = diameter(geometry)
    radius = d / 2
    if distance is None:
        start_distance = radius
    else:
        start_distance = max(0.0, distance - radius)
    return d, start_distance


def _line_through_centroid_perpendicular_to_point(
        geometry: shapely.geometry.base.BaseGeometry,
        point: shapely.Point) -> shapely.LineString:
    # line through the centroid to the point, extending equally on either side
    start = shapely.affinity.rotate(point, angle=180, origin=geometry.centroid)
    line = shapely.LineString([start, point])
    # rotate the line to be perpendicular
    line = shapely.affinity.rotate(line, angle=90, origin=geometry.centroid)
    # extend the line past the geometry
    scale = line.length / diameter(geometry)
    return shapely.affinity.scale(line, xfact=scale, yfact=scale)


def _chord_perpendicular_to_point(geometry: shapely.geometry.base.BaseGeometry,
                                  point: shapely.Point) -> shapely.LineString:
    line = _line_through_centroid_perpendicular_to_point(geometry, point)
    # return only the portion of the line that intersects the input
    result = line.intersection(geometry)
    # if the line is discontinuous, take the longest piece
    if isinstance(result, shapely.MultiLineString):
        result = max(result.geoms, key=lambda g: g.length)
    return result
