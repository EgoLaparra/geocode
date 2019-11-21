import psycopg2

conn = psycopg2.connect("dbname=geometries user=egoitz password=egoitz")
cursor = conn.cursor()


SQL = {"geometry":          {"query": """select geom from geometries 
                                where osm_id = '%s' and osm_type = '%s'  
                                and st_geometrytype(geom) != 'ST_MultiPoint';""",
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
       "area":              {"query": """select st_area('%s');""",
                             "single_output": True},
       "length":            {"query": """select st_length('%s');""",
                             "single_output": True},
       "median":            {"query": """select st_geometricmedian(st_points('%s'));""",
                             "single_output": True},
       "centroid":          {"query": """select st_centroid('%s');""",
                             "single_output": True},
       "envelope":          {"query": """select st_points(st_envelope('%s'));""",
                             "single_output": True},
       "isempty":           {"query": """select st_isempty('%s');""",
                             "single_output": True},
       "isclosed":          {"query": """select st_isclosed('%s');""",
                             "single_output": True},
       "iscollection":      {"query": """select st_iscollection('%s');""",
                             "single_output": True},
       "isclosed_list":     {"query": """select st_isclosed(geom) from (values %s) as t (geom);""",
                             "single_output": False},
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
       "linemerge":         {"query": """select st_linemerge('%s');""",
                             "single_output": True},
       "union":             {"query": """select st_union('%s');""",
                             "single_output": True},
       "union_list":        {"query": """select st_union(geom) from (values %s) as t (geom);""",
                             "single_output": True},
       "intersection":      {"query": """select st_intersection('%s', '%s');""",
                             "single_output": True},
       "translate":         {"query": """select st_translate('%s', %s, %s);""",
                             "single_output": True},
       "makepolygon":       {"query": """select st_makepolygon('%s');""",
                             "single_output": True},
       "transform":         {"query": """select st_transform(st_setsrid(st_astext('%s'), 4326), 3857) as geom;""",
                             "single_output": True},
       "geography":         {"query": """select Geography('%s') as geom;""",
                             "single_output": True},
       "buffer":            {"query": """select st_makevalid(st_buffer('%s', %s));""",
                             "single_output": True}
       }


def execute_query(sql_query_key, geometry):
    sql_query = SQL[sql_query_key]
    cursor.execute(sql_query["query"] % geometry)
    if sql_query["single_output"]:
        return cursor.fetchone()[0]
    else:
        return cursor.fetchall()


def get_value_list(geometry_list):
    return ",".join(["('%s')" % g for g in geometry_list])


def dataframe_fromsql(geometry, dataframe):
    sql_query = SQL["geography"]
    return dataframe.from_postgis(sql_query["query"] % geometry, conn)
    return dataframe.from_postgis(geometry, conn)