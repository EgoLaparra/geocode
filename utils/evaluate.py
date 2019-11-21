import geometries as geo
import numpy as np


class Scores:
    def __init__(self):
        self.overlap_score = np.array([0., 0., 0.])
        self.shape_score = np.array([0., 0., 0.])
        self.distances = np.array([0., 0., 0.])
        # self.hausdorff_score = 0.


def to_km(value):
    return value/1000000


def transform_to_geography(gold_geometry, predicted_geometry):
    gold_geography = geo.transform_geometry(gold_geometry)
    predicted_geography = geo.transform_geometry(predicted_geometry)
    return gold_geography, predicted_geography


def score_shape(gold_geometry, predicted_geometry, skip_transform=False):
    if not skip_transform:
        gold_geometry, predicted_geometry = transform_to_geography(gold_geometry, predicted_geometry)

    if geo.geometry_isempty(predicted_geometry):
        predicted_geography_translated = predicted_geometry
    else:
        gold_centrality = geo.get_centrality(gold_geometry, "centroid")
        predicted_centrality = geo.get_centrality(predicted_geometry, "centroid")
        gold_centrality_coordinates = geo.get_coordinates(gold_centrality)
        predicted_centrality_coordinates = geo.get_coordinates(predicted_centrality)
        translation = (gold_centrality_coordinates[0] - predicted_centrality_coordinates[0],
                       gold_centrality_coordinates[1] - predicted_centrality_coordinates[1])
        predicted_geography_translated = geo.translate_geometry(predicted_geometry, translation)
    return score_overlap(gold_geometry, predicted_geography_translated, skip_transform=True)


def score_overlap(gold_geometry, predicted_geometry, skip_transform=False):
    if not skip_transform:
        gold_geometry, predicted_geometry = transform_to_geography(gold_geometry, predicted_geometry)

    buffer_offset = 1e-10
    gold_geometry = geo.apply_buffer(gold_geometry, buffer_offset)
    predicted_geometry = geo.apply_buffer(predicted_geometry, buffer_offset)
    overlap_geometry = geo.intersect_geometries([gold_geometry, predicted_geometry])
    gold_area = geo.get_geometry_area(gold_geometry)
    predicted_area = geo.get_geometry_area(predicted_geometry)
    overlap_area = geo.get_geometry_area(overlap_geometry)

    p = overlap_area / predicted_area if predicted_area > 0 else 0.
    r = overlap_area / gold_area if gold_area > 0 else 0.
    f = 2 * p * r / (p + r) if (p > 0 or r > 0) else 0.
    return p, r, f


def score_distances(gold_geometry, predicted_geometry, skip_transform=False):
    if not skip_transform:
        gold_geometry, predicted_geometry = transform_to_geography(gold_geometry, predicted_geometry)

    if geo.geometry_isempty(predicted_geometry):
        return 20000000, 20000000, 20000000
    else:
        gold_centrality = geo.get_centrality(gold_geometry, "centroid")
        predicted_centrality = geo.get_centrality(predicted_geometry, "centroid")
        centroid_distance = geo.calculate_distance(gold_centrality, predicted_centrality)

        gold_centrality = geo.get_centrality(gold_geometry, "median")
        predicted_centrality = geo.get_centrality(predicted_geometry, "median")
        median_distance = geo.calculate_distance(gold_centrality, predicted_centrality)

        min_distance = geo.calculate_distance(gold_geometry, predicted_geometry)

        return centroid_distance, median_distance, min_distance


def score_hausdorff_distance(gold_geometry, predicted_geometry, skip_transform=False):
    if not skip_transform:
        gold_geometry, predicted_geometry = transform_to_geography(gold_geometry, predicted_geometry)

    if geo.geometry_isempty(predicted_geometry):
        hausdorff_distance = 20000000
    else:
        hausdorff_distance = geo.calculate_hausdorff_distance(gold_geometry, predicted_geometry)

    return hausdorff_distance


def update_scores(global_scores, local_scores):
    global_scores.overlap_score += local_scores.overlap_score
    global_scores.shape_score += local_scores.shape_score
    # global_scores.hausdorff_score += local_scores.hausdorff_score
    global_scores.distances += local_scores.distances


def print_scores(scores, norm=1):
    print("Overlap:")
    print("P: %s\tR: %s\tF: %s" % tuple(scores.overlap_score / norm))
    print("Shape:")
    print("P: %s\tR: %s\tF: %s" % tuple(scores.shape_score / norm))
    # print("Hausdorff distance: %s" % (scores.hausdorff_score / norm))
    print("Centroid distance: %s\tMedian distance: %s\tMin distance: %s" % tuple(scores.distances / norm))


def score(gold_geometry, predicted_geometry, skip_transform=False, print_it=False):
    if not skip_transform:
        gold_geometry, predicted_geometry = transform_to_geography(gold_geometry, predicted_geometry)

    overlap_p, overlap_r, overlap_f = score_overlap(gold_geometry, predicted_geometry, skip_transform=True)
    shape_p, shape_r, shape_f = score_shape(gold_geometry, predicted_geometry, skip_transform=True)
    # hausdorff_distance = score_hausdorff_distance(gold_geometry, predicted_geometry, skip_transform=True)
    distances = score_distances(gold_geometry, predicted_geometry, skip_transform=False)

    scores = Scores()
    scores.overlap_score = np.array([overlap_p, overlap_r, overlap_f])
    scores.shape_score = np.array([shape_p, shape_r, shape_f])
    scores.distances = distances
    # scores.hausdorff_score = hausdorff_distance

    if print_it:
        print_scores(scores)

    return scores

