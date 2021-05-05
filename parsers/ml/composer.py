import sys
import csv
import argparse
import traceback
from lxml import etree
from operator import itemgetter
from math import pi, cos, sin, sqrt
from shapely.geometry import Polygon, LineString, Point
from shapely import wkt
from shapely import affinity, ops


from geometries import Geometries
import spatial_relate as sr


def circle(center, radius, points):
    circle_points = []
    for p in range(points + 1):
        angle = p * 2 * pi / points
        x = center.x + radius * cos(angle)
        y = center.y + radius * sin(angle)
        circle_points.append((x, y))
    return LineString(circle_points)


def arc(center, radius, points, azimuth):
    arc_size = 45 / 360 * 2 * pi
    start_angle = azimuth * arc_size - (arc_size / 2)
    arc_points = []
    center_x = float(center.x)
    center_y = float(center.y)
    for p in range(points + 1):
        angle = start_angle + p * arc_size / points
        x = center_x + radius * cos(angle)
        y = center_y + radius * sin(angle)
        arc_points.append([x, y])
    return LineString(arc_points)


def cone(center, radius, points, azimuth):
    cone_arc = arc(center, radius, points, azimuth)
    center_x = float(center.x)
    center_y = float(center.y)
    cone_points = [[center_x, center_y]]
    cone_points.extend([[coord[0], coord[1]] for coord in cone_arc.coords])
    cone_points.append([center_x, center_y])
    return Polygon(cone_points)


def projection(center, radius, azimuth):
    arc_size = 45 / 360 * 2 * pi
    angle = azimuth * arc_size
    x = radius * cos(angle)
    y = radius * sin(angle)
    return affinity.translate(center, x, y)


def translate_azimuth(azimuth):
    azimuth = 10 - azimuth
    return azimuth if azimuth < 8 else azimuth - 8


def reverse_azimuth(azimuth):
    azimuth = azimuth - 4
    return azimuth if azimuth >= 0 else 8 - azimuth


def split_geometry(geometry, line):
    splits = []
    if geometry.geom_type == "Point":
        splits.append(geometry)
    elif geometry.geom_type == "GeometryCollection":
        for geom in geometry:
            splits.extend(
                split_geometry(geom, line)
            )
    else:
        splits = ops.split(geometry, line).geoms
    return splits


def complete_hull(geom_a, geom_b, difference=False):
    point_a = affinity.rotate(geom_a.centroid, 90, origin=geom_b.centroid)
    point_b = affinity.rotate(geom_a.centroid, -90, origin=geom_b.centroid)
    crossing_line = LineString([point_a, point_b])
    splits = []
    for split in split_geometry(geom_b, crossing_line):
        distance = geom_a.distance(split)
        splits.append((distance, split))
    split = min(splits, key=itemgetter(0))[1]
    hull = ops.unary_union([geom_a, split]).convex_hull
    return hull if not difference else hull.difference(split)


def calculate_spatial_relation(geometry, relation, relation_geometry):
    if relation == "Disjoint" and not geometry.disjoint(relation_geometry):
        if geometry.crosses(relation_geometry):
            geometry = geometry.difference(relation_geometry)
    elif relation == "Touches" and not geometry.touches(relation_geometry):
        if geometry.disjoint(relation_geometry):
            geometry = complete_hull(geometry, relation_geometry, difference=True)
        elif geometry.crosses(relation_geometry):
            geometry = geometry.difference(relation_geometry)
    elif relation == "Intersects" and not geometry.intersects(relation_geometry):
        if geometry.disjoint(relation_geometry) or geometry.touches(relation_geometry):
            geometry = complete_hull(geometry, relation_geometry)
    elif relation == "Contains" and not geometry.contains(relation_geometry):
        if geometry.crosses(relation_geometry) or geometry.within(relation_geometry):
            geometry = geometry.intersection(relation_geometry)
    elif relation == "Within" and not geometry.within(relation_geometry):
        if geometry.crosses(relation_geometry) or geometry.contains(relation_geometry):
            geometry = geometry.intersection(relation_geometry)
    return geometry


def calculate_spatial_relations(geometry, reference_data):
    for reference_geometry, reference_geometry_data in reference_data:
        relation = reference_geometry_data[0]
        geometry = calculate_spatial_relation(geometry, relation, reference_geometry)
    return geometry


def compose_arcs(reference_data):
    closest_points = []
    for i in range(len(reference_data)):
        for j in range(i + 1, len(reference_data)):
            arc_i = reference_data[i][1][3]
            arc_j = reference_data[j][1][3]
            p_i, p_j = ops.nearest_points(arc_i, arc_j)
            closest_points.extend([p_i, p_j])
    return ops.unary_union(closest_points).centroid


def buffer_to_area(prediction, size):
    if size > 0:
        radius = sqrt(size/pi)
        return prediction.centroid.buffer(radius)
    else:
        return prediction


def load_size(entity, size_predictions):
    size_prediction = size_predictions[entity.get("id")]
    size_mantissa = int(size_prediction[0][1])
    size_exponent = int(size_prediction[1][1])
    return sr.ldexp10(size_mantissa, size_exponent) / 100000


def load_reference_data(geom, entity, relation_predictions):
    reference_data = []
    for link in entity.xpath(".//link"):
        relation_prediction = relation_predictions[link.get("id")]

        link_geometry = geom.get_entity_geometry(link)
        link_geometry = wkt.loads(geom.as_text(link_geometry))

        relation = relation_prediction[0][1]

        centroid = geom.get_centrality(link_geometry)
        centroid = wkt.loads(geom.as_text(centroid))

        azimuth = int(relation_prediction[1][1])
        azimuth = translate_azimuth(azimuth)
        azimuth = reverse_azimuth(azimuth)

        distance_mantissa = int(relation_prediction[2][1])
        distance_exponent = int(relation_prediction[3][1])
        distance = sr.ldexp10(distance_mantissa, distance_exponent) / 1000

        link_arc = arc(centroid, distance, 20, azimuth)

        data = [relation, azimuth, distance, link_arc]
        reference_data.append((link_geometry, data))
    return reference_data


def load_relation_predictions(prediction_file, gold=False):
    predictions = {}
    with open(prediction_file) as predfile:
        predrows = csv.reader(predfile, delimiter='\t')
        for row in predrows:
            if gold:
                predictions[row[2]] = [[row[5], row[7]],
                                       [row[10], row[12]],
                                       [row[15], row[17]],
                                       [row[20], row[22]]]
            else:
                predictions[row[2]] = [[row[5], row[6]],
                                       [row[10], row[11]],
                                       [row[15], row[16]],
                                       [row[20], row[21]]]
    return predictions


def load_size_predictions(prediction_file, gold=False):
    predictions = {}
    with open(prediction_file) as predfile:
        predrows = csv.reader(predfile, delimiter='\t')
        for row in predrows:
            if gold:
                predictions[row[0]] = [[row[4], row[5]],
                                       [row[9], row[10]]]
            else:
                predictions[row[0]] = [[row[4], row[6]],
                                       [row[9], row[11]]]
    return predictions


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Compose spatial relations.')
    parser.add_argument('-d', '--data_file', dest="data_file", metavar="FILE",
                        help='XML file with data.')
    parser.add_argument('-s', '--size', dest="size_file", metavar="FILE",
                        help='TSV file with size predictions.')
    parser.add_argument('-r', '--relations', dest="relations_file", metavar="FILE",
                        help='TSV file with relation predictions.')
    parser.add_argument('-t', '--table', dest="table_name", type=str,
                        help='Table name to store the outputs.')
    parser.add_argument('-g', '--gold', dest="use_gold", action="store_true",
                        help='Use gold data.')
    args = parser.parse_args()

    geom = Geometries()
    size_predictions = load_size_predictions(args.size_file, gold=args.use_gold)
    relation_predictions = load_relation_predictions(args.relations_file, gold=args.use_gold)
    data_source = etree.parse(args.data_file)
    for record_id, entity in enumerate(data_source.xpath("//entity[@status='5']")):
        entity_id = entity.get("id")
        try:
            print("Composing entity %s..." % entity_id)
            size = load_size(entity, size_predictions)
            reference_data = load_reference_data(geom, entity, relation_predictions)
            prediction = compose_arcs(reference_data)
            prediction = buffer_to_area(prediction, size)
            prediction = calculate_spatial_relations(prediction, reference_data)
            geom.database.insert_in_table(args.table_name, record_id, entity_id, prediction)
        except KeyError:
            traceback.print_exc(file=sys.stdout)
