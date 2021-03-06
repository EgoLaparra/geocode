import sys
from lxml import etree

import evaluate
from plots import plot_geometries
from geometries import Geometries


def area_baselines(geom, reference_geometries):
    max_baseline = None
    min_baseline = None
    for reference_geometry in reference_geometries:
        reference_buffered_geometry = geom.apply_buffer(reference_geometry, 1e-8)
        geometry_area = geom.get_geometry_area(reference_buffered_geometry)
        if max_baseline is None or geometry_area > max_baseline[1]:
            max_baseline = (reference_geometry, geometry_area)
        if min_baseline is None or geometry_area < min_baseline[1]:
            min_baseline = (reference_geometry, geometry_area)
    return max_baseline[0], min_baseline[0]


def union_baseline(geom, reference_geometries):
    return geom.unite_geometries(reference_geometries)


def intersection_baseline(geom, reference_geometries):
    return geom.intersect_geometries(reference_geometries)


def run(data_file):
    data = etree.parse(data_file)
    plot_it = False
    gold_entities = data.xpath('//entity[@status="5"]')
    num_gold_entities = len(gold_entities)
    max_scores = evaluate.Scores(total_gold=num_gold_entities)
    min_scores = evaluate.Scores(total_gold=num_gold_entities)
    union_scores = evaluate.Scores(total_gold=num_gold_entities)
    intersection_scores = evaluate.Scores(total_gold=num_gold_entities)
    geom = Geometries()
    for e, gold_entity in enumerate(gold_entities):
        print("Gold entity: %s %s" % (gold_entity.get("id"), gold_entity.get("wikipedia")))
        gold_geometry = geom.get_entity_geometry(gold_entity)
        max_fetched = geom.database.select_from_table("max_baseline_output", gold_entity.get("id"))
        min_fetched = geom.database.select_from_table("min_baseline_output", gold_entity.get("id"))
        union_fetched = geom.database.select_from_table("union_baseline_output", gold_entity.get("id"))
        intersection_fetched = geom.database.select_from_table("intersection_baseline_output", gold_entity.get("id"))

        reference_geometries = []
        if max_fetched is None or min_fetched is None or union_fetched is None or intersection_fetched is None:
            for reference_entity in gold_entity.xpath('.//link'):
                print("\tReference entity: %s %s" % (reference_entity.get("id"), reference_entity.get("wikipedia")))
                reference_geometry = geom.get_entity_geometry(reference_entity)
                reference_geometries.append(reference_geometry)
        else:
            print("\tEntity already parsed.")
        print("")

        if max_fetched is None or min_fetched is None:
            max_baseline, min_baseline = area_baselines(reference_geometries)
            geom.database.insert_in_table("max_baseline_output", e, gold_entity.get("id"), max_baseline)
            geom.database.insert_in_table("min_baseline_output", e, gold_entity.get("id"), min_baseline)
        else:
            max_baseline = max_fetched[0]
            min_baseline = min_fetched[0]
        evaluate.update_scores(max_scores,
                               evaluate.score(geom, gold_geometry, max_baseline))
        evaluate.update_scores(min_scores,
                               evaluate.score(geom, gold_geometry, min_baseline))

        if union_fetched is None:
            union = union_baseline(reference_geometries)
            geom.database.insert_in_table("union_baseline_output", e, gold_entity.get("id"), union)
        else:
            union = union_fetched[0]
        evaluate.update_scores(union_scores,
                               evaluate.score(geom, gold_geometry, union))

        if intersection_fetched is None:
            intersection = intersection_baseline(reference_geometries)
            geom.database.insert_in_table("intersection_baseline_output", e, gold_entity.get("id"), intersection)
        else:
            intersection = intersection_fetched[0]
        evaluate.update_scores(intersection_scores,
                               evaluate.score(geom, gold_geometry, intersection))

        if plot_it:
            plot_geometries([gold_geometry, max_baseline, min_baseline, union, intersection],
                            ["mediumseagreen", "coral", "khaki", "navy", "orchid"])

    geom.close_connection()

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


if __name__ == "__main__":
    run(sys.argv[1])