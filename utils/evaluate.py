import sys
import numpy as np
from lxml import etree

from geometries import Geometries


class Scores:
    def __init__(self, total_gold=1, total_predicted=0):
        self.overlap_score = np.array([0., 0., 0.])
        self.overlap_score_x2 = np.array([0., 0., 0.])
        self.envelope_score = np.array([0., 0., 0.])
        self.envelope_score_x2 = np.array([0., 0., 0.])
        self.total_gold = total_gold
        self.total_predicted = total_predicted

    def global_score(self, local_p, local_r, predicted=False):
        global_p = local_p / self.total_predicted if self.total_predicted > 0 else 0
        if predicted:
            global_r = local_r / self.total_predicted if self.total_predicted > 0 else 0
        else:
            global_r = local_r / self.total_gold if self.total_gold > 0 else 0
        global_f = 2 * global_p * global_r / (global_p + global_r) if (global_p > 0 and global_r > 0) else 0
        return global_p, global_r, global_f

    def global_overlap(self, predicted=False):
        return [tuple(self.global_score(self.overlap_score[0], self.overlap_score[1], predicted)),
                tuple(self.global_score(self.overlap_score_x2[0], self.overlap_score_x2[1], predicted))]

    def global_envelope(self, predicted=False):
        return [tuple(self.global_score(self.envelope_score[0], self.envelope_score[1], predicted)),
                tuple(self.global_score(self.envelope_score_x2[0], self.envelope_score_x2[1], predicted))]

    def coverage(self):
        return self.total_predicted / self.total_gold


def to_km(value, area=False):
    if area:
        return value / 1000000
    else:
        return value / 1000

def out_of_limits(geom, geometry):
    bounding_diagonal = geom.get_bounding_diagonal(geometry)
    lower_point, upper_point = geom.dump_points(bounding_diagonal)
    lower_x, lower_y = geom.get_coordinates(lower_point)
    upper_x, upper_y = geom.get_coordinates(upper_point)
    if lower_x < -180 or lower_y < -90 or upper_x > 180 or upper_y > 90:
        return True
    else:
        return False
    
def transform_to_geography(geom, gold_geometry, predicted_geometry):
    gold_geography = geom.transform_geometry(gold_geometry)
    predicted_geography = geom.transform_geometry(predicted_geometry)
    return gold_geography, predicted_geography


def scale_geometry(geom, geometry, scale_factor):
    factor_point = geom.from_text("POINT(%s %s)" % (scale_factor, scale_factor))
    origin = geom.get_centrality(geometry)
    if not geom.contains(geometry, origin):
        origin = geom.get_point_on_surface(geometry)
    scaled_geometry = geom.scale_geometry(geometry, factor_point, origin)
    return geom.unite_geometries([geometry, scaled_geometry])


def score_overlap(geom, gold_geometry, predicted_geometry, envelope=False, skip_transform=False):
    if not skip_transform:
        gold_geometry, predicted_geometry = transform_to_geography(geom, gold_geometry, predicted_geometry)
    if envelope:
        gold_geometry = geom.get_oriented_envelope(gold_geometry)

    overlap_geometry = geom.intersect_geometries([gold_geometry, predicted_geometry])
    gold_area = geom.get_geometry_area(gold_geometry)
    predicted_area = geom.get_geometry_area(predicted_geometry)
    overlap_area = geom.get_geometry_area(overlap_geometry)
    p = overlap_area / predicted_area if predicted_area > 0 else 0.
    r = overlap_area / gold_area if gold_area > 0 else 0.
    f = 2 * p * r / (p + r) if (p > 0 and r > 0) else 0.
    return p, r, f


def score_scaled(geom, gold_geometry, predicted_geometry, scale_factor=2., envelope=False, skip_transform=False):
    if not skip_transform:
        gold_geometry, predicted_geometry = transform_to_geography(geom, gold_geometry, predicted_geometry)
    if envelope:
        gold_geometry = geom.get_oriented_envelope(gold_geometry)
    gold_scaled_geometry = scale_geometry(geom, gold_geometry, scale_factor)
    p, _, _ = score_overlap(geom, gold_scaled_geometry, predicted_geometry, envelope, skip_transform=True)
    predicted_scaled_geometry = scale_geometry(geom, predicted_geometry, scale_factor)
    _, r, _ = score_overlap(geom, gold_geometry, predicted_scaled_geometry, envelope, skip_transform=True)
    return p, r, 0.


def update_scores(global_scores, local_scores):
    if local_scores is not None:
        global_scores.overlap_score += local_scores.overlap_score
        global_scores.overlap_score_x2 += local_scores.overlap_score_x2
        global_scores.envelope_score += local_scores.envelope_score
        global_scores.envelope_score_x2 += local_scores.envelope_score_x2
        global_scores.total_predicted += 1


def print_scores(scores, tabular=""):
    overlaps = scores.global_overlap()
    print(tabular + "Strict:")
    print(tabular + "P: %s\tR: %s\tF: %s" % overlaps[0])
    print(tabular + "Px2: %s\tRx2: %s" % overlaps[1][:2])
    overlaps = scores.global_overlap(predicted=True)
    print(tabular + "Strict (predicted):")
    print(tabular + "P: %s\tR: %s\tF: %s" % overlaps[0])
    print(tabular + "Px2: %s\tRx2: %s" % overlaps[1][:2])
    envelopes = scores.global_envelope()
    print(tabular + "Relaxed:")
    print(tabular + "P: %s\tR: %s\tF: %s" % envelopes[0])
    print(tabular + "Px2: %s\tRx2: %s" % envelopes[1][:2])
    envelopes = scores.global_envelope(predicted=True)
    print(tabular + "Relaxed (predicted):")
    print(tabular + "P: %s\tR: %s\tF: %s" % envelopes[0])
    print(tabular + "Px2: %s\tRx2: %s" % envelopes[1][:2])
    if tabular == "":
        print("Coverage: %s" % scores.coverage())


def score(geom, gold_geometry, predicted_geometry, skip_transform=False, print_it=False):
    if not skip_transform:
        gold_geometry, predicted_geometry = transform_to_geography(geom, gold_geometry, predicted_geometry)
        gold_geometry = buffer_geometry(geom, gold_geometry)
        predicted_geometry = buffer_geometry(geom, predicted_geometry)

    if geom.geometry_isempty(predicted_geometry):
        return None
    else:
        overlap = score_overlap(geom, gold_geometry, predicted_geometry,
                                skip_transform=True)
        overlap_x2 = score_scaled(geom, gold_geometry, predicted_geometry,
                                  skip_transform=True)
        envelope = score_overlap(geom, gold_geometry, predicted_geometry,
                                 envelope=True, skip_transform=True)
        envelope_x2 = score_scaled(geom, gold_geometry, predicted_geometry,
                                   envelope=True, skip_transform=True)
        scores = Scores(total_predicted=1)
        scores.overlap_score = np.array([overlap[0], overlap[1], overlap[2]])
        scores.overlap_score_x2 = np.array([overlap_x2[0], overlap_x2[1], overlap_x2[2]])
        scores.envelope_score = np.array([envelope[0], envelope[1], envelope[2]])
        scores.envelope_score_x2 = np.array([envelope_x2[0], envelope_x2[1], envelope_x2[2]])
        if print_it:
            print_scores(scores)
        return scores


def buffer_geometry(geom, geometry, buffer_radius=0.5):
    geometry_type = geom.get_geometry_type(geometry)
    if geometry_type != "ST_Polygon" and geometry_type != "ST_MultiPolygon":
        geometry = geom.apply_buffer(geometry, buffer_radius)
    return geometry


def evaluate(gold_file, prediction_table):
    gold_data = etree.parse(gold_file)
    gold_entities = gold_data.xpath('//entity[@status="5"]')
    num_gold_entities = len(gold_entities)
    scores = Scores(total_gold=num_gold_entities)
    geom = Geometries()
    for gold_entity in gold_entities:
        try:
            print("Gold entity: %s %s" % (gold_entity.get("id"), gold_entity.get("wikipedia")))
            gold_geometry = geom.get_entity_geometry(gold_entity)
            predicted_geometry = geom.get_predicted_geometry(prediction_table, gold_entity.get("id"))
            if len(predicted_geometry) > 0 and not geom.geometry_isempty(predicted_geometry):
                if out_of_limits(geom, predicted_geometry):
                    raise Exception("Latitude or longitude exceeded limits.")
                predicted_geometry = geom.unite_geometry(geom.from_text(geom.as_text(predicted_geometry)))
                entity_scores = score(geom, gold_geometry, predicted_geometry, False)
                print_scores(entity_scores, tabular="\t")
                update_scores(scores, entity_scores)
            else:
                print("\tNo geometry for %s in %s" % (gold_entity.get("id"), prediction_table))
        except Exception as e:
            print("\tException: %s" % e)
            num_gold_entities -= 1
            pass
    print_scores(scores)
    geom.close_connection()


if __name__ == "__main__":
    evaluate(sys.argv[1], sys.argv[2])
