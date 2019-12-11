import sys
from lxml import etree

import evaluate
from plots import plot_geometries
import geometries as geo


def area_baselines(reference_geometries):
    max_baseline = None
    min_baseline = None
    for reference_geometry in reference_geometries:
        reference_buffered_geometry = geo.apply_buffer(reference_geometry, 1e-8)
        geometry_area = geo.get_geometry_area(reference_buffered_geometry)
        if max_baseline is None or geometry_area > max_baseline[1]:
            max_baseline = (reference_geometry, geometry_area)
        if min_baseline is None or geometry_area < min_baseline[1]:
            min_baseline = (reference_geometry, geometry_area)
    return max_baseline[0], min_baseline[0]


def union_baseline(reference_geometries):
    return geo.unite_geometries(reference_geometries)


def intersection_baseline(reference_geometries):
    return geo.intersect_geometries(reference_geometries)


def get_entity_geometry(entity):
    osm_ids = entity.get("osm").split(" ")
    osm_types = entity.get("type").split(" ")
    entity_geometry = []
    for osm_id, osm_type in zip(osm_ids, osm_types):
        for geometry in geo.get_geometries(osm_id, osm_type):
            geometry = geo.process_geometry(geometry)
            entity_geometry.append(geometry)
    if len(entity_geometry) == 1:
        return entity_geometry[0]
    elif len(entity_geometry) > 1:
        return geo.unite_geometries(entity_geometry)
    else:
        raise Exception("No geometries for %s %s" % (" ".join(osm_ids), " ".join(osm_types)))


if __name__ == "__main__":
    sample = etree.parse(sys.argv[1])
    plot_it = False
    gold_entities = sample.xpath('//entity[@status="5"]')
    num_gold_entities = len(gold_entities)
    max_scores = evaluate.Scores(total_gold=num_gold_entities)
    min_scores = evaluate.Scores(total_gold=num_gold_entities)
    union_scores = evaluate.Scores(total_gold=num_gold_entities)
    intersection_scores = evaluate.Scores(total_gold=num_gold_entities)

    for gold_entity in gold_entities:
        print("Gold entity: %s %s" % (gold_entity.get("id"), gold_entity.get("wikipedia")))
        gold_geometry = get_entity_geometry(gold_entity)

        reference_geometries = []
        for reference_entity in gold_entity.xpath('.//link'):
            print("\tReference entity: %s %s" % (reference_entity.get("id"), reference_entity.get("wikipedia")))
            reference_geometry = get_entity_geometry(reference_entity)
            reference_geometries.append(reference_geometry)
        print("")

        max_baseline, min_baseline = area_baselines(reference_geometries)
        evaluate.update_scores(max_scores,
                               evaluate.score(gold_geometry, max_baseline))
        evaluate.update_scores(min_scores,
                               evaluate.score(gold_geometry, min_baseline))
        union = union_baseline(reference_geometries)
        evaluate.update_scores(union_scores,
                               evaluate.score(gold_geometry, union))
        intersection = intersection_baseline(reference_geometries)
        evaluate.update_scores(intersection_scores,
                               evaluate.score(gold_geometry, intersection))

        if plot_it:
            plot_geometries([gold_geometry, max_baseline, min_baseline, union, intersection],
                            ["mediumseagreen", "coral", "khaki", "navy", "orchid"])

    print("Max geom:")
    evaluate.print_scores(max_scores)
    print("")
    print("Min geom:")
    evaluate.print_scores(min_scores)
    print("")
    print("Union:")
    evaluate.print_scores(union_scores)
    print("")
    print("Intersection:")
    evaluate.print_scores(intersection_scores)
    print("")
