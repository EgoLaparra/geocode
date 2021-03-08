from database import Database


class Geometries:

    def __init__(self):
        self.database = Database()

    def as_text(self, geometry):
        return self.database.execute_query("as_text", geometry)

    def from_text(self, string):
        return self.database.execute_query("from_text", string)

    def dump_geometry(self, geometry):
        return self.database.execute_query("dump", geometry)

    def dump_points(self, geometry):
        return self.database.execute_query("dumppoints", geometry)

    def apply_buffer(self, geometry, offset):
        return self.database.execute_query("buffer", (geometry, offset))

    def geometry_isempty(self, geometry):
        return self.database.execute_query("isempty", geometry)

    def get_geometry_type(self, geometry):
        return self.database.execute_query("type", geometry)

    def get_geometry_area(self, geometry):
        return self.database.execute_query("area", geometry)

    def get_geometry_length(self, geometry):
        return self.database.execute_query("length", geometry)

    def get_coordinates(self, geometry):
        x = self.database.execute_query("x", geometry)
        y = self.database.execute_query("y", geometry)
        return x, y

    def get_centrality(self, geometry, metric="centroid"):
        centrality = self.database.execute_query(metric, geometry)
        return self.database.execute_query("closest_point", (geometry, centrality))

    def get_max(self, geometry):
        xmax = self.database.execute_query("xmax", geometry)
        ymax = self.database.execute_query("ymax", geometry)
        return xmax, ymax

    def get_min(self, geometry):
        xmin = self.database.execute_query("xmin", geometry)
        ymin = self.database.execute_query("ymin", geometry)
        return xmin, ymin

    def get_point_on_surface(self, geometry):
        return self.database.execute_query("point_on_surface", geometry)

    def get_envelope(self, geometry):
        return self.database.execute_query("envelope", geometry)

    def get_oriented_envelope(self, geometry):
        return self.database.execute_query("oriented_envelope", geometry)

    def get_bounding_circle(self, geometry):
        return self.database.execute_query("bounding_circle", geometry)

    def get_bounding_diagonal(self, geometry):
        return self.database.execute_query("bounding_diagonal", geometry)

    def contains(self, geometry_a, geometry_b):
        return self.database.execute_query("contains", (geometry_a, geometry_b))

    def instersects(self, geometry_a, geometry_b):
        return self.database.execute_query("intersects", (geometry_a, geometry_b))

    def calculate_distance(self, geometry_a, geometry_b):
        return self.database.execute_query("distance", (geometry_a, geometry_b))

    def calculate_max_distance(self, geometry_a, geometry_b):
        return self.database.execute_query("max_distance", (geometry_a, geometry_b))

    def calculate_hausdorff_distance(self, geometry_a, geometry_b):
        return self.database.execute_query("hausdorff", (geometry_a, geometry_b))

    def intersect_geometries(self, geometry_list):
        result = geometry_list[0]
        for geometry in geometry_list[1:]:
            result = self.database.execute_query("intersection", (result, geometry))
        return result

    def unite_geometry(self, geometry):
        return self.database.execute_query("union", geometry)

    def unite_geometries(self, geometry_list):
        geometry_values = self.database.get_value_list(geometry_list)
        return self.database.execute_query("union_list", geometry_values)

    def collect_geometries(self, geometry_list):
        geometry_values = self.database.get_value_list(geometry_list)
        return self.database.execute_query("collect", geometry_values)

    def translate_geometry(self, geometry, translation):
        return self.database.execute_query("translate", (geometry, translation[0], translation[1]))

    def scale_geometry(self, geometry, factor, origin):
        return self.database.execute_query("scale", (geometry, factor, origin))

    def make_geography(self, geometry):
        return self.database.execute_query("geography", geometry)

    def transform_geometry(self, geometry):
        return self.database.execute_query("transform", geometry)

    def simplify_geometry(self, geometry, segments=2):
        envelope = self.dump_points(
            self.get_envelope(geometry)
        )
        if len(envelope) == 1:
            return [[envelope[0]] * (segments + 1) for i in range(segments + 1)]
        else:
            simple_geometry = [[None] * (segments + 1) for i in range(segments + 1)]
            new_x_set = set()
            new_y_set = set()
            i = 0
            j = 0
            increments = [(0, 1), (1, 0), (0, -1), (-1, 0)]
            for e, point in enumerate(envelope[:-1], 1):
                i_increment, j_increment = increments[e - 1]
                closest_to_point = self.database.execute_query("closest_point", (geometry, point[0]))
                simple_geometry[i][j] = closest_to_point
                i += i_increment
                j += j_increment
                source_x, source_y = self.get_coordinates(point)
                target_x, target_y = self.get_coordinates(envelope[e])
                for segment in range(1, segments):
                    segment_x = source_x + (target_x - source_x) * segment / segments
                    if segment_x != source_x and segment_x != target_x:
                        new_x_set.add(segment_x)
                    segment_y = source_y + (target_y - source_y) * segment / segments
                    if segment_y != source_y and segment_y != target_y:
                        new_y_set.add(segment_y)
                    segment_point = self.from_text("POINT(%s %s)" % (segment_x, segment_y))
                    closest_to_segment_point = self.database.execute_query("closest_point", (geometry, segment_point))
                    simple_geometry[i][j] = closest_to_segment_point
                    i += i_increment
                    j += j_increment
            for i, new_x in enumerate(sorted(new_x_set), 1):
                for j, new_y in enumerate(sorted(new_y_set), 1):
                    inner_point = self.from_text("POINT(%s %s)" % (new_x, new_y))
                    closest_to_inner_point = self.database.execute_query("closest_point", (geometry, inner_point))
                    simple_geometry[i][j] = closest_to_inner_point
            return simple_geometry

    def process_geometry(self, geometry):
        geometry_type = self.database.execute_query("type", geometry)
        if geometry_type == "ST_MultiLineString" or geometry_type == "ST_LineString":
            geometry = self.database.execute_query("linemerge", geometry)
            geometry_is_collection = self.database.execute_query("iscollection", geometry)
            if geometry_is_collection:
                geometry = self.process_geometry_collection(geometry)
            else:
                geometry_isclosed = self.database.execute_query("isclosed", geometry)
                if geometry_isclosed:
                    geometry = self.database.execute_query("makepolygon", geometry)
            return geometry
        elif geometry_type == "ST_Point" or geometry_type == "ST_MultiPoint":
            return geometry[0]
        else:
            print(self.as_text(self.database.execute_query("linemerge", geometry)))
            raise Exception("Not LineString or MultiLineString or ST_Point or ST_MultiPoint: %s" % geometry_type)

    def process_geometry_collection(self, geometry_collection):
        geometry_dump = [g[0] for g in self.database.execute_query("dump", geometry_collection)]
        for g, geometry_value in enumerate(geometry_dump):
            if self.database.execute_query("isclosed", geometry_value):
                geometry_dump[g] = self.database.execute_query("makepolygon", geometry_value)
        geometry_values = self.database.get_value_list(geometry_dump)
        return self.database.execute_query("union_list", geometry_values)

    def get_entity_geometry(self, entity):
        osm_ids = entity.get("osm").split(" ")
        osm_types = entity.get("type").split(" ")
        entity_geometry = []
        for osm_id, osm_type in zip(osm_ids, osm_types):
            for geometry in self.get_geometries(osm_id, osm_type):
                geometry = self.process_geometry(geometry)
                entity_geometry.append(geometry)
        if len(entity_geometry) == 1:
            return entity_geometry[0]
        elif len(entity_geometry) > 1:
            return self.unite_geometries(entity_geometry)
        else:
            raise Exception("No geometries for %s %s" % (" ".join(osm_ids), " ".join(osm_types)))

    def get_geometries(self, osm, otype):
        return self.database.execute_query("geometry", (osm, otype))

    def get_predicted_geometry(self, table, entity_id):
        entity_geometry = self.database.execute_query("prediction", (table, entity_id))
        if len(entity_geometry) == 1:
            return entity_geometry[0]
        elif len(entity_geometry) > 1:
            return self.unite_geometries(entity_geometry)
        return entity_geometry

    def make_geodataframe(self, geometry, dataframe):
        geodataframe = self.database.dataframe_from_sql(geometry, dataframe)
        geodataframe = geodataframe.to_crs(epsg=3857)
        return geodataframe

    def make_raster(self, width, height, left_x, upper_y, scale_x, scale_y):
        return self.database.execute_query("makeemptyraster", (width, height, left_x, upper_y, scale_x, scale_y))

    def raster_width(self, raster):
        return self.database.execute_query("width", (raster))

    def geometry_as_raster(self, geometry, raster):
        return self.database.execute_query("asraster", (geometry, raster))

    def unite_rasters(self, raster1, raster2):
        return self.database.execute_query("uniterasters", (raster1, raster2))

    def raster_pixels(self, raster):
        return self.database.execute_query("rasteraspixels", (raster))

    def pixel_as_polygon(self, raster, x, y):
        return self.database.execute_query("pixelaspolygon", (raster, x, y))

    def pixel_as_polygons(self, raster):
        return self.database.execute_query("pixelaspolygons", (raster))

    def close_connection(self):
        self.database.close()
