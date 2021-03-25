import math


def frexp10(x):
    exp = int(math.log10(x))
    return x / 10**exp, exp


def geometry_size(geom, geometry, geometry_type="ST_Polygon", discrete=True):
    size = frexp10(
        geom.get_geometry_area(geometry) * 1000000 if geometry_type == "ST_Polygon"
        else geom.get_geometry_length(geometry) * 1000
    )
    return int(size[0]) if discrete else size[0], size[1]


def reference_azimuth(geom, geometry_a, geometry_b, discrete=True):
    azimuth = (
        geom.calculate_azimuth(
            geom.get_centrality(geometry_a),
            geom.get_centrality(geometry_b)
        ) + 22.5
    ) / 45
    return math.floor(azimuth) if discrete else azimuth


def reference_distance(geom, geometry_a, geometry_b, discrete=True):
    distance = frexp10(
        geom.calculate_distance(
            geom.get_centrality(geometry_a),
            geom.get_centrality(geometry_b)
        ) * 1000
    )
    return int(distance[0]) if discrete else distance[0], distance[1]
