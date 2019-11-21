import sys
from lxml import etree

import evaluate
from plots import plot_geometries
import geometries as geo


def area_baselines(reference_geometries):
    max_baseline = None
    min_baseline = None
    for reference_geometry in reference_geometries:
        geometry_area = geo.get_geometry_area(reference_geometry)
        geometry_type = geo.get_geometry_type(reference_geometry)
        if max_baseline is None or geometry_area > max_baseline[1]:
            max_baseline = (reference_geometry, geometry_area)
        if (min_baseline is None or geometry_area < min_baseline[1]) and geometry_type != "ST_Point":
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
        # print(osm_id, osm_type)
        for geometry in geo.get_geometries(osm_id, osm_type):
            geometry = geo.process_geometry(geometry)
            entity_geometry.append(geometry)
    if len(entity_geometry) == 1:
        return entity_geometry[0]
    else:
        return geo.unite_geometries(entity_geometry)


if __name__ == "__main__":
    sample = etree.parse(sys.argv[1])
    plot_it = False
    max_scores = evaluate.Scores()
    min_scores = evaluate.Scores()
    union_scores = evaluate.Scores()
    intersection_scores = evaluate.Scores()
    gold_entities = sample.xpath('//entity[@status="5"]')
    print(len(gold_entities))
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
        evaluate.update_scores(max_scores, evaluate.score(gold_geometry, max_baseline, skip_transform=True, print_it=False))
        evaluate.update_scores(min_scores, evaluate.score(gold_geometry, min_baseline, skip_transform=True, print_it=False))
        union = union_baseline(reference_geometries)
        evaluate.update_scores(union_scores, evaluate.score(gold_geometry, union, skip_transform=True, print_it=False))
        intersection = intersection_baseline(reference_geometries)
        evaluate.update_scores(intersection_scores, evaluate.score(gold_geometry, intersection, skip_transform=True, print_it=False))

        if plot_it:
            plot_geometries([gold_geometry, max_baseline, min_baseline, union, intersection],
                            ["mediumseagreen", "coral", "khaki", "navy", "orchid"])

    print("Max geom:")
    evaluate.print_scores(max_scores, norm=len(gold_entities))
    print("")
    print("Min geom:")
    evaluate.print_scores(min_scores, norm=len(gold_entities))
    print("")
    print("Union:")
    evaluate.print_scores(union_scores, norm=len(gold_entities))
    print("")
    print("Intersection:")
    evaluate.print_scores(intersection_scores, norm=len(gold_entities))
    print("")
