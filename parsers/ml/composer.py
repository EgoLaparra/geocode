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
from evaluate import Scores, score, print_scores, update_scores


class GeomData:

    def __init__(self, id, geometry):
        self.id = id
        self.postgis_geometry = geometry
        self.postgis_centroid = None
        self.geometry = None
        self.centroid = None

    def to_shapely(self, geom):
        self.geometry = wkt.loads(geom.as_text(self.postgis_geometry))
        self.postgis_centroid = geom.get_centrality(self.postgis_geometry)
        self.centroid = self.geometry.centroid

    @staticmethod
    def from_xml_and_geom(entity, geom):
        geom_data = GeomData(entity.get("id"),
                             geom.get_entity_geometry(entity))
        geom_data.to_shapely(geom)
        return geom_data


class LinkData(GeomData):

    def __init__(self, id, geometry):
        super().__init__(id, geometry)
        self.relation = None
        self.distance = None
        self.azimuth = None
        self.arc = None

    def set_relation(self, relation):
        self.relation = relation

    def set_distance(self, distance):
        self.distance = distance

    def set_azimuth(self, azimuth):
        self.azimuth = azimuth

    def set_arc(self, arc):
        self.arc = arc

    def load_link_data(self, relation_predictions):
        relation_prediction = relation_predictions[self.id]
        relation = relation_prediction[0][1]
        self.set_relation(relation)

        azimuth = int(relation_prediction[1][1])
        azimuth = reverse_azimuth(azimuth)
        self.set_azimuth(azimuth)

        distance_mantissa = int(relation_prediction[2][1])
        distance_exponent = int(relation_prediction[3][1])
        distance = sr.ldexp10(distance_mantissa, distance_exponent) / 1000
        self.set_distance(distance)

        link_arc = arc(self.centroid, self.distance, 20, self.azimuth)
        self.set_arc(link_arc)

    def calculate_link_gold_data(self, geom, entity, distance_discrete=True, round_to=1, arc_as_polygon=False):
        distance_mantissa, distance_exponent = sr.reference_distance(geom, entity.centroid, self.centroid,
                                                                     discrete=distance_discrete, round_to=round_to)
        distance = sr.ldexp10(distance_mantissa, distance_exponent) / 1000
        self.set_distance(distance)

        if arc_as_polygon:
            distance1 = sr.ldexp10(distance_mantissa - 0.5, distance_exponent) / 1000
            distance2 = sr.ldexp10(distance_mantissa + 0.5, distance_exponent) / 1000
            link_arc1 = arc(self.centroid, distance1, 20, self.azimuth)
            link_arc2 = arc(self.centroid, distance2, 20, self.azimuth)
            link_arc = Polygon(list(link_arc1.coords) + link_arc2.coords[::-1] + link_arc1.coords[:1])
        else:
            link_arc = arc(self.centroid, self.distance, 20, self.azimuth)
        self.set_arc(link_arc)


    @staticmethod
    def from_xml_and_geom(entity, geom):
        link_data = LinkData(entity.get("id"),
                             geom.get_entity_geometry(entity))
        link_data.to_shapely(geom)
        return link_data


class EntityData(GeomData):

    def __init__(self, id, geometry):
        super().__init__(id, geometry)
        self.links = []
        self.size = None

    def add_links(self, link_data):
        self.links.append(link_data)

    def set_size(self, size):
        self.size = size

    def load_size(self, size_predictions):
        size_prediction = size_predictions[self.id]
        size_mantissa = int(size_prediction[0][1])
        size_exponent = int(size_prediction[1][1])
        size = sr.ldexp10(size_mantissa, size_exponent) / 1000000
        self.set_size(size)

    def load_reference_data(self, relation_predictions):
        for link_data in self.links:
            link_data.load_link_data(relation_predictions)

    def calculate_gold_size(self, geom):
        entity_type = geom.get_geometry_type(self.geometry)
        size_real_m, size_real_e = sr.geometry_size(geom, self.geometry, entity_type)
        size = sr.ldexp10(size_real_m, size_real_e) / 1000000
        self.set_size(size)

    def calculate_gold_reference_data(self, geom, distance_discrete=True, round_to=1, arc_as_polygon=False):
        for link_data in self.links:
            link_data.calculate_link_gold_data(geom, self, distance_discrete, round_to, arc_as_polygon)

    @staticmethod
    def from_xml_and_geom(entity, geom):
        entity_data = EntityData(entity.get("id"),
                                 geom.get_entity_geometry(entity))
        entity_data.to_shapely(geom)
        for link in entity.xpath(".//link"):
            link_data = LinkData.from_xml_and_geom(link, geom)
            entity_data.add_links(link_data)
        return entity_data


def circle(center, radius, points):
    circle_points = []
    for p in range(points + 1):
        angle = p * 2 * pi / points
        x = center.x + radius * sin(angle)
        y = center.y + radius * cos(angle)
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
        x = center_x + radius * sin(angle)
        y = center_y + radius * cos(angle)
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
    x = radius * sin(angle)
    y = radius * cos(angle)
    return affinity.translate(center, x, y)


def reverse_azimuth(azimuth):
    azimuth = azimuth - 4
    return azimuth if azimuth >= 0 else 8 + azimuth


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


def calculate_spatial_relation(geometry, link):
    if link.relation == "Disjoint" and not geometry.disjoint(link.geometry):
        if geometry.crosses(link.geometry):
            geometry = geometry.difference(link.geometry)
    elif link.relation == "Touches" and not geometry.touches(link.geometry):
        if geometry.disjoint(link.geometry):
            geometry = complete_hull(geometry, link.geometry, difference=True)
        elif geometry.crosses(link.geometry):
            geometry = geometry.difference(link.geometry)
    elif link.relation == "Intersects" and not geometry.intersects(link.geometry):
        if geometry.disjoint(link.geometry) or geometry.touches(link.geometry):
            geometry = complete_hull(geometry, link.geometry)
    elif link.relation == "Contains" and not geometry.contains(link.geometry):
        if geometry.crosses(link.geometry) or geometry.within(link.geometry):
            geometry = geometry.intersection(link.geometry)
    elif link.relation == "Within" and not geometry.within(link.geometry):
        if geometry.crosses(link.geometry) or geometry.contains(link.geometry):
            geometry = geometry.intersection(link.geometry)
    return geometry


def calculate_spatial_relations(geometry, links):
    for link in links:
        geometry = calculate_spatial_relation(geometry, link)
    return geometry


def compose_arcs(links):
    closest_points = []
    for i in range(len(links)):
        for j in range(i + 1, len(links)):
            arc_i = links[i].arc
            arc_j = links[j].arc
            if arc_i.intersects(arc_j):
                arc_intersection = arc_i.intersection(arc_j)
                if arc_intersection.geom_type == "Point":
                    closest_points.append(arc_intersection)
            else:
                closest_points.extend(
                    [point for point in ops.nearest_points(arc_j, arc_i)]
                )
    return ops.unary_union(closest_points).centroid


def compose_arc_polygons(links):
    total_arc_intersection = None
    for i in range(len(links)):
        for j in range(i + 1, len(links)):
            arc_i = links[i].arc
            arc_j = links[j].arc
            if arc_i.intersects(arc_j):
                arc_intersection = arc_i.intersection(arc_j)
                if total_arc_intersection is None:
                    total_arc_intersection = arc_intersection
                elif arc_intersection.intersects(total_arc_intersection):
                    total_arc_intersection = arc_intersection.intersection(total_arc_intersection)
    return total_arc_intersection.centroid


def buffer_to_area(geometry, size):
    if size > 0:
        radius = sqrt(size/pi)
        return geometry.centroid.buffer(radius)
    else:
        return geometry


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
                predictions[row[0]] = [[row[4], row[6]],
                                       [row[9], row[11]]]
            else:
                predictions[row[0]] = [[row[4], row[5]],
                                       [row[9], row[10]]]
    return predictions


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Compose spatial relations.')
    parser.add_argument('-d', '--data_file', dest="data_file", metavar="FILE",
                        help='XML file with data.')
    parser.add_argument('-s', '--size', dest="size_file", metavar="FILE",
                        help='TSV file with size predictions.')
    parser.add_argument('-r', '--relations', dest="relations_file", metavar="FILE",
                        help='TSV file with relation predictions.')
    parser.add_argument('-t', '--table', dest="table_name", type=str, default=None,
                        help='Table name to store the outputs.')
    parser.add_argument('-e', '--evaluate', dest="do_evaluation", action="store_true",
                        help='Calculate scores.')
    parser.add_argument('-g', '--gold', dest="use_gold", action="store_true",
                        help='Use gold data.')
    parser.add_argument('--discrete', dest="distance_discrete", action="store_true",
                        help='Calculate gold distance as discrete value.')
    parser.add_argument('--round_to', type=int, default=1,
                        help='Round to this value when calculating gold distance.')
    parser.add_argument('--arc_as_polygon', action="store_true",
                        help='Calculate gold arcs as Polygon instead of LineString.')
    args = parser.parse_args()

    geom = Geometries()
    size_predictions = load_size_predictions(args.size_file, gold=args.use_gold)
    relation_predictions = load_relation_predictions(args.relations_file, gold=args.use_gold)
    data_source = etree.parse(args.data_file)
    gold_entities = data_source.xpath("//entity[@status='5']")[:5]
    if args.do_evaluation:
        num_gold_entities = len(gold_entities)
        scores = Scores(total_gold=num_gold_entities)
    for record_id, entity in enumerate(gold_entities):
        try:
            entity_data = EntityData.from_xml_and_geom(entity, geom)
            if args.table_name is not None and \
                    geom.database.select_from_table(args.table_name, entity_data.id) is not None:
                print("Entity %s already in %s" % (entity_data.id, args.table_name))
            else:
                print("Composing entity %s..." % entity_data.id)
                entity_data.load_size(size_predictions)
                entity_data.load_reference_data(relation_predictions)

                if args.use_gold:
                    entity_data.calculate_gold_size(geom)
                    entity_data.calculate_gold_reference_data(geom, args.distance_discrete,
                                                              args.round_to, args.arc_as_polygon)

                if args.arc_as_polygon:
                    prediction = compose_arc_polygons(entity_data.links)
                else:
                    prediction = compose_arcs(entity_data.links)
                    prediction = buffer_to_area(prediction, entity_data.size)
                prediction = calculate_spatial_relations(prediction, entity_data.links)

                if args.do_evaluation:
                    entity_scores = score(geom, entity_data.postgis_geometry, prediction)
                    print_scores(entity_scores, tabular="\t")
                    update_scores(scores, entity_scores)
                if args.table_name is not None:
                    geom.database.insert_in_table(args.table_name, record_id, entity_data.id, prediction)
        except Exception:
            traceback.print_exc(file=sys.stdout)
    if args.do_evaluation:
        print_scores(scores)
    geom.close_connection()
