import numpy as np

from sql_queries import execute_query, get_value_list, dataframe_fromsql


def as_text(geometry):
    return execute_query("as_text", geometry)


def from_text(string):
    return execute_query("from_text", string)


def dump_geometry(geometry):
    return execute_query("dump", geometry)


def apply_buffer(geometry, offset):
    return execute_query("buffer", (geometry, offset))


def geometry_isempty(geometry):
    return execute_query("isempty", geometry)


def get_geometry_type(geometry):
    return execute_query("type", geometry)


def get_geometry_area(geometry):
    return execute_query("area", geometry)


def get_geometry_length(geometry):
    return execute_query("length", geometry)


def get_coordinates(geometry):
    x = execute_query("x", geometry)
    y = execute_query("y", geometry)
    return x, y


def get_centrality(geometry, metric):
    centrality = execute_query(metric, geometry)
    return execute_query("closest_point", (geometry, centrality))


def get_envelope(geometry):
    envelope = execute_query("envelope", geometry)
    return execute_query("dump", envelope)


def calculate_distance(geometry_a, geometry_b):
    return execute_query("distance", (geometry_a, geometry_b))


def calculate_max_distance(geometry_a, geometry_b):
    return execute_query("max_distance", (geometry_a, geometry_b))


def calculate_hausdorff_distance(geometry_a, geometry_b):
    return execute_query("hausdorff", (geometry_a, geometry_b))


def intersect_geometries(geometry_list):
    result = geometry_list[0]
    for geometry in geometry_list[1:]:
        result = execute_query("intersection", (result, geometry))
    return result


def unite_geometries(geometry_list):
    geometry_values = get_value_list(geometry_list)
    return execute_query("union_list", geometry_values)


def translate_geometry(geometry, translation):
    return execute_query("translate", (geometry, translation[0], translation[1]))


def make_geography(geometry):
    return execute_query("geography", geometry)


def transform_geometry(geometry):
    return execute_query("transform", geometry)


def process_geometry(geometry):
    geometry_type = execute_query("type", geometry)
    if geometry_type == "ST_MultiLineString" or geometry_type == "ST_LineString":
        geometry = execute_query("linemerge", geometry)
        geometry_iscollection = execute_query("iscollection", geometry)
        if geometry_iscollection:
            geometry_dump = [g[0] for g in execute_query("dump", geometry)]
            geometry_values = get_value_list(geometry_dump)
            geometry_list_isclosed = execute_query("isclosed_list", geometry_values)
            if np.any(geometry_list_isclosed):
                geometry_numpoints = execute_query("numpoints_list", geometry_values)
                argmax_numpoints = np.argmax(geometry_numpoints)
                geometry = geometry_dump[argmax_numpoints]
            else:
                geometry = execute_query("union_list", geometry_values)

        geometry_isclosed = execute_query("isclosed", geometry)
        if geometry_isclosed:
            geometry = execute_query("makepolygon", geometry)

    elif geometry_type == "ST_Point" or geometry_type == "ST_MultiPoint":
        geometry = geometry[0]
    else:
        print(as_text(execute_query("linemerge", geometry)))
        raise Exception("Not LineString or MultiLineString or ST_Point or ST_MultiPoint: %s" % geometry_type)

    return geometry


def get_geometries(osm, otype):
    return execute_query("geometry", (osm, otype))


def make_geodataframe(geometry, dataframe):
    geodataframe = dataframe_fromsql(geometry, dataframe)
    geodataframe = geodataframe.to_crs(epsg=3857)
    return geodataframe
