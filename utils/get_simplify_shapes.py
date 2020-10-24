from geometries import Geometries
from lxml import etree
import argparse

def get_entities_fromXML(xml_filepath):
    collection = etree.parse(xml_filepath)
    all_entities = collection.xpath('//entity')

    return all_entities

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--xml_filepath', default='../../geocode-data/test/test.xml', type=str,
                        help='path of data collections')
    parser.add_argument('--sample_size', default=50, type=int,
                        help='number of sample datas')
    parser.add_argument('--output_dir', default='../geocode-data/collection_samples', type=str,
                        help='path of data collections samples')
    args = parser.parse_args()
    geom = Geometries()

    entities = get_entities_fromXML(args.xml_filepath)
    all_entity_coordinates = {}
    for entity in entities:
        osm_ids = entity.get("osm").split(" ")
        osm_types = entity.get("type").split(" ")
        temp_key = '_'.join(osm_ids+osm_types)
        entity_geometry = geom.get_entity_geometry(entity)
        simplified_geometry = geom.simplify_geometry(entity_geometry, segments=2)
        entity_coordinates_list = []
        for polygon_list in simplified_geometry:
            coordinates = []
            for polygon in polygon_list:
                coordinates.append(geom.get_coordinates(polygon))
            entity_coordinates_list.append(coordinates)
        print(entity_coordinates_list)
        all_entity_coordinates[temp_key]=entity_coordinates_list
    assert len(entities) == len(list(all_entity_coordinates.keys()))
    geom.close_connection()