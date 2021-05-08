import math
import re


def frexp10(x):
    exp = math.floor(math.log10(x))
    return x / 10**exp, exp


def ldexp10(x, exp):
    return x * 10**exp


def geometry_size(geom, geometry, geometry_type="ST_Polygon", discrete=True):
    size = frexp10(
        geom.get_geometry_area(geometry) * 1000000
        if geometry_type == "ST_Polygon" or geometry_type == "ST_MultiPolygon"
        else geom.get_geometry_length(geometry) * 1000
    )
    return round(size[0]) if discrete else size[0], size[1]


def reference_azimuth(geom, geometry_a, geometry_b, discrete=True):
    azimuth = (
        geom.calculate_azimuth(
            geom.get_centrality(geometry_a),
            geom.get_centrality(geometry_b)
        ) + 22.5
    ) / 45
    return math.floor(azimuth) if discrete else azimuth


def reference_distance(geom, geometry_a, geometry_b, discrete=True, round_to=1):
    distance = frexp10(
        geom.calculate_distance(
            geom.get_centrality(geometry_a),
            geom.get_centrality(geometry_b)
        ) * 1000
    )
    return round(distance[0], round_to) if discrete else distance[0], distance[1]


def project_centroid(geom, reference_geometry, reference_distance, reference_azimuth):
    return geom.project_geometry(
        geom.get_centrality(reference_geometry),
        ldexp10(reference_distance[0], reference_distance[1]) / 1000,
        reference_azimuth * 45
    )


def buffer_centroid(geom, target_centroid, geometry_type, geometry_size):
    geometry_size = ldexp10(geometry_size[0], geometry_size[1])
    radius = (
                 math.sqrt(geometry_size / math.pi)
                 if geometry_type == "ST_Polygon" or geometry_type == "ST_MultiPolygon"
                 else geometry_size / 2
              ) / 1000
    return geom.apply_buffer(target_centroid, radius)


def equivalent_relation(relate_matrix):
    relation = []
    if re.match(r'^[^F].F..FFF.$', relate_matrix) is not None:
        relation = "Equals"
    elif re.match(r'^FF.FF.{4}$', relate_matrix) is not None:
        relation = "Disjoint"
    elif re.match(r'^[^F].{5}FF.$', relate_matrix) is not None:
        relation = "Contains"
    elif re.match(r'^([^F].{5}FF.|.[^F].{4}FF.|.{3}[^F]..FF.|.{3}[^F].FF.)$', relate_matrix) is not None:
        relation = "Covers"
    elif re.match(r'^[^F].F..F.{3}$', relate_matrix) is not None:
        relation = "Within"
    elif re.match(r'^([^F].F..F.{3}|.[^F]F..F.{3}|..F[^F].F.{3}|..F.[^F]F.{3})$', relate_matrix) is not None:
        relation = "CoveredBy"
    elif re.match(r'^(F[^F].{7}|F..[^F].{5}|F.{3}[^F].{4})$', relate_matrix) is not None:
        relation = "Touches"
    elif re.match(r'^([^F].{8}|.[^F].{7}|.{3}[^F].{5}|.{4}[^F].{4})$', relate_matrix) is not None:
        relation = "Intersects"
    elif relation is None:
        raise Exception("Incorrect relate matrix: %s" % relate_matrix)
    return relation
