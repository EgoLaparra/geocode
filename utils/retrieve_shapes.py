from lxml import etree
import pickle as pkl
import overpy
import sys
import os
import time
import http

api = overpy.Overpass()


def get_point(over_obj):
    return float(over_obj.lon), float(over_obj.lat)


def get_line(over_obj):
    return [get_point(node) for node in over_obj.nodes]


def get_polygon(overpass_object, osm_type):
    if osm_type == "relation":
        ways = ["(%s)" % ",".join(["%s %s" % t for t in get_line(way)]) for way in overpass_object.ways]
        nodes = ["(%s %s)" % get_point(node) for node in overpass_object.nodes]
        polygon = []
        if len(ways) > 0:
            polygon.append("MULTILINESTRING(%s)" % (",".join(ways)))
        if len(nodes) > 0:
            polygon.append("MULTIPOINT(%s)" % (",".join(nodes)))
        return polygon, overpass_object.relations[0].tags, overpass_object.relations[0].attributes
    elif osm_type == "way" and len(overpass_object.ways) > 0:
        way = "LINESTRING(%s)" % ",".join(["%s %s" % t for t in get_line(overpass_object.ways[0])])
        return [way], overpass_object.ways[0].tags, overpass_object.ways[0].attributes
    elif osm_type == "node" and len(overpass_object.nodes) > 0:
        node = "POINT(%s %s)" % get_point(overpass_object.nodes[0])
        return [node], overpass_object.nodes[0].tags, overpass_object.nodes[0].attributes
    return None, None, None


def retrieve_polygon(osm_type, osm_id):
    overpass_query = """%s(%s);(._;>;);out meta;""" % (osm_type, osm_id)
    overpass_result = None
    while overpass_result is None:
        try:
            overpass_result = api.query(overpass_query)
            if osm_type == "relation" and len(overpass_result.ways) == 0 and len(overpass_result.nodes) == 0:
                members = overpass_result.relations[0].members
                if len(members) > 0:
                    relations_query = "".join(["relation(%s);" % relation.ref for relation in members])
                    overpass_query = """(%s);(._;>;);out meta;""" % relations_query
                    overpass_result = None
                else:
                    print("No polygon for %s %s" % (osm_type, osm_id))
        except overpy.exception.OverpassTooManyRequests:
            print("Too many requests! Wait for it...")
            time.sleep(10)
        except overpy.exception.OverpassGatewayTimeout:
            print("Server load too high! Wait for it...")
            time.sleep(10)
        except http.client.IncompleteRead:
            print("Incomplete read. Try again.")
        except overpy.exception.OverPyException as ex:
            print("Some overpass error with: %s %s" % (osm_type, osm_id))
            print(ex)
    return overpass_result


def create_file_paths(intput_path):
    if os.path.isfile(intput_path):
        return[intput_path]
    else:
        return [os.path.join(intput_path, input_file) for input_file in os.listdir(intput_path)]


def retrieve_polygon_dictionary(gl_paths, output_pkl_file, polygon_dictionary, dump_dictionary=False):
    with (open(output_pkl_file, "ab") if dump_dictionary else None) as pklfile:
        for gl_path in gl_paths:
            gl_root = etree.parse(gl_path)
            for e, entity in enumerate(gl_root.xpath('/data/entities//*[(self::entity and @status="5") or (self::link and ancestor::entity[@status="5"])]')):
                for osm_id, osm_type in zip(entity.get('osm').split(" "), entity.get('type').split(" ")):
                    osm_key = (osm_id, osm_type)
                    osm_key = " ".join(osm_key)
                    if osm_key not in polygon_dictionary:
                        overpass_result = retrieve_polygon(osm_type, osm_id)
                        if overpass_result is not None:
                            polygon, tags, attributes = get_polygon(overpass_result, osm_type)
                            polygon_dictionary[osm_key] = {"id": osm_key, "tags": tags, "attributes": attributes, "polygon": polygon}
                            pkl.dump(polygon_dictionary[osm_key], pklfile)
                if e % 5 == 0:
                    print(e)


def write_sql_script(polygon_dictionary, script_file_path):
    with open(script_file_path, 'w') as script_file:
        script_file.write("CREATE DATABASE geometries;\n\n")
        script_file.write("\\c geometries\n\n")
        script_file.write("CREATE EXTENSION postgis;\n\n")
        script_file.write("CREATE TABLE IF NOT EXISTS geometries (osm_id varchar, osm_type varchar, geom geometry, PRIMARY KEY (osm_id, osm_type));\n\n")
        script_file.write("INSERT INTO geometries VALUES\n")
        polygon_rows = []
        for osm_key in polygon_dictionary:
            osm_id, osm_type = osm_key.split(" ")
            if polygon_dictionary[osm_key]["polygon"] is not None:
                for geometry in polygon_dictionary[osm_key]["polygon"]:
                        polygon_rows.append("\t('%s', '%s', '%s')" % (osm_id, osm_type, geometry))
        script_file.write("%s ON CONFLICT DO NOTHING;\n\n" % ",\n".join(polygon_rows))
        script_file.write("SELECT COUNT(*) FROM geometries;\n")


def load_dictionary(output_pkl_file):
    polygon_dictionary = {}
    if os.path.exists(output_pkl_file):
        with open(output_pkl_file, "rb") as pklfile:
            try:
                while True:
                    polygon = pkl.load(pklfile)
                    polygon_dictionary[polygon["id"]] = polygon
            except EOFError:
                pass
    return polygon_dictionary


if __name__ == "__main__":
    input_path = sys.argv[1]
    output_script_file = sys.argv[2]
    output_pkl_file = os.path.splitext(output_script_file)[0] + ".pkl"
    file_paths = create_file_paths(input_path)
    polygon_dictionary = load_dictionary(output_pkl_file)
    retrieve_polygon_dictionary(file_paths, output_pkl_file, polygon_dictionary, dump_dictionary=True)
    write_sql_script(polygon_dictionary, output_script_file)
