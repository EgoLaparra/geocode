import psycopg2


SQL = {"geometry":          {"query": """select geom from geometries 
                                where osm_id = '%s' and osm_type = '%s';""",
                             "single_output": False},
       "as_text":           {"query": """select st_astext('%s');""",
                             "single_output": True},
       "from_text":         {"query": """select st_geomfromtext('%s');""",
                             "single_output": True},
       "type":              {"query": """select st_geometrytype('%s');""",
                             "single_output": True},
       "x":                 {"query": """select st_x('%s');""",
                             "single_output": True},
       "y":                 {"query": """select st_y('%s');""",
                             "single_output": True},
       "xmax":              {"query": """select st_xmax('%s');""",
                             "single_output": True},
       "ymax":              {"query": """select st_ymax('%s');""",
                             "single_output": True},
       "xmin":              {"query": """select st_xmin('%s');""",
                             "single_output": True},
       "ymin":              {"query": """select st_ymin('%s');""",
                             "single_output": True},
       "area":              {"query": """select st_area('%s');""",
                             "single_output": True},
       "length":            {"query": """select st_length('%s');""",
                             "single_output": True},
       "median":            {"query": """select st_geometricmedian(st_points('%s'));""",
                             "single_output": True},
       "centroid":          {"query": """select st_centroid('%s');""",
                             "single_output": True},
       "point_on_surface":  {"query": """select st_pointonsurface('%s');""",
                             "single_output": True},
       "envelope":          {"query": """select st_envelope('%s'::geometry);""",
                             "single_output": True},
       "oriented_envelope": {"query": """select st_orientedenvelope('%s');""",
                             "single_output": True},
       "bounding_circle":   {"query": """select st_minimumboundingcircle('%s');""",
                             "single_output": True},
       "bounding_diagonal": {"query": """select st_boundingdiagonal('%s');""",
                             "single_output": True},
       "isempty":           {"query": """select st_isempty('%s'::geometry);""",
                             "single_output": True},
       "isclosed":          {"query": """select st_isclosed('%s');""",
                             "single_output": True},
       "iscollection":      {"query": """select st_iscollection('%s');""",
                             "single_output": True},
       "isclosed_list":     {"query": """select st_isclosed(geom) from (values %s) as t (geom);""",
                             "single_output": False},
       "isvalid":           {"query": """select st_isvalid('%s'::geometry);""",
                             "single_output": True},
       "contains":          {"query": """select st_contains('%s', '%s');""",
                             "single_output": True},
       "intersects":        {"query": """select st_intersects('%s', '%s');""",
                             "single_output": True},
       "numpoints":         {"query": """select st_numpoints('%s');""",
                             "single_output": True},
       "numpoints_list":    {"query": """select st_numpoints(geom) from (values %s) as t (geom);""",
                             "single_output": False},
       "closest_point":     {"query": """select st_closestpoint('%s', '%s');""",
                             "single_output": True},
       "distance":          {"query": """select st_distance('%s', '%s');""",
                             "single_output": True},
       "max_distance":      {"query": """select st_maxdistance('%s', '%s');""",
                             "single_output": True},
       "hausdorff":         {"query": """select st_hausdorffdistance('%s', '%s');""",
                             "single_output": True},
       "dump":              {"query": """select (st_dump('%s')).geom;""",
                             "single_output": False},
       "dumppoints":        {"query": """select (st_dumppoints('%s')).geom;""",
                             "single_output": False},
       "linemerge":         {"query": """select st_linemerge('%s');""",
                             "single_output": True},
       "collect":           {"query": """select st_collect(geom) from (values %s) as t (geom);""",
                             "single_output": True},
       "union":             {"query": """select st_union('%s'::geometry);""",
                             "single_output": True},
       "union_list":        {"query": """select st_union(geom) from (values %s) as t (geom);""",
                             "single_output": True},
       "intersection":      {"query": """select st_intersection('%s', '%s');""",
                             "single_output": True},
       "translate":         {"query": """select st_translate('%s', %s, %s);""",
                             "single_output": True},
       "scale":             {"query": """select st_scale('%s', '%s'::geometry, '%s');""",
                             "single_output": True},
       "makepolygon":       {"query": """select st_makepolygon('%s');""",
                             "single_output": True},
       "transform":         {"query": """select st_transform(st_setsrid(st_astext('%s'), 4326), 3857) as geom;""",
                             "single_output": True},
       "geography":         {"query": """select Geography('%s') as geom;""",
                             "single_output": True},
       "buffer":            {"query": """select st_makevalid(st_buffer('%s', %s));""",
                             "single_output": True},
       "make_valid":        {"query": """select st_makevalid('%s');""",
                             "single_output": True},
       "prediction":        {"query": """select geom from %s 
                                where entity_id = '%s';""",
                             "single_output": False},
       "makeemptyraster":   {"query": """select st_makeemptyraster(%s, %s, %s, %s, %s, %s, 0, 0);""",
                             "single_output": True},
       "width":             {"query": """select st_width('%s');""", 
                             "single_output": True},
       "asraster":          {"query": """select st_asraster('%s', '%s', touched => true);""", 
                             "single_output": True},
       "uniterasters":      {"query": """select st_union(raster::raster, 'MAX'::text) from 
                                (select ('%s') as raster UNION select ('%s') as raster) foo;""",
                             "single_output": True},
       "rasteraspixels":    {"query": """select (pixels).* from (select st_pixelofvalue('%s',  1) as pixels) as foo;""", 
                             "single_output": False},
       "pixelaspolygon":    {"query": """select st_pixelaspolygon('%s', %s, %s);""", 
                             "single_output": True},
       "pixelaspolygons":   {"query": """select (polygons).geom from 
                                (select st_pixelaspolygons('%s') as polygons) as foo;""",
                             "single_output": False}
       }


class Database:

    conn = None
    cursor = None

    def __init__(self):
        self.open()
        self.cursor = self.conn.cursor()

    def open(self):
        self.conn = psycopg2.connect("dbname=geometries user=guest password=guest host=localhost")

    def close(self):
        self.conn.close()

    def execute_query(self, sql_query_key, parameters):
        try:
            sql_query = SQL[sql_query_key]
            self.cursor.execute(sql_query["query"] % parameters)
            if sql_query["single_output"]:
                fetched = self.cursor.fetchone()[0]
            else:
                fetched = self.cursor.fetchall()
            return fetched
        except Exception:
            self.close()
            raise

    def insert_in_table(self, table, record_id, entity_id, geom):
        try:
            sql_insert_query = "insert into %s (id, entity_id, geom) values ('%s', '%s', '%s');"
            self.cursor.execute(sql_insert_query % (table, record_id, entity_id, geom))
            self.conn.commit()
        except Exception:
            self.close()
            raise

    def select_from_table(self, table, entity_id):
        try:
            sql_select_query = "select geom from %s where entity_id = '%s';"
            self.cursor.execute(sql_select_query % (table, entity_id))
            return self.cursor.fetchone()
        except Exception:
            self.close()
            raise

    @staticmethod
    def get_value_list(geometry_list):
        return ",".join(["('%s')" % g for g in geometry_list])

    def dataframe_from_sql(self, geometry, dataframe):
        try:
            sql_query = SQL["geography"]
            return dataframe.from_postgis(sql_query["query"] % geometry, self.conn)
        except Exception:
            self.close()
            raise

