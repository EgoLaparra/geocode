from geometries import Geometries
from lxml import etree
import argparse
import pickle
import sys
import os

def pickle_dump_large_file(obj, filepath):
    max_bytes = 2**31 - 1
    bytes_out = pickle.dumps(obj)
    n_bytes = sys.getsizeof(bytes_out)
    with open(filepath, 'wb') as f_out:
        for idx in range(0, n_bytes, max_bytes):
            f_out.write(bytes_out[idx:idx + max_bytes])

def pickle_load_large_file(filepath):
    max_bytes = 2**31 - 1
    input_size = os.path.getsize(filepath)
    bytes_in = bytearray(0)
    with open(filepath, 'rb') as f_in:
        for _ in range(0, input_size, max_bytes):
            bytes_in += f_in.read(max_bytes)
    obj = pickle.loads(bytes_in)
    return obj

def get_entities_fromXML(xml_filepath):
    collection = etree.parse(xml_filepath)
    all_entities = collection.xpath('//entity')

    return all_entities

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--xml_filepath_train', default='../../geocode-data/collection_samples/train_samples.xml', type=str,
                        help='path of data collections')
    parser.add_argument('--sample_size', default=50, type=int,
                        help='number of sample datas')
    parser.add_argument('--output_dir_train', default='../../geocode-data/collection_samples/model_input_train.pkl', type=str,
                        help='path of data collections samples')
    args = parser.parse_args()
    geom = Geometries()

    entities = get_entities_fromXML(args.xml_filepath_train)
    all_entity_coordinates = {}
    for entity in entities:
        entity_id = entity.get("id")
        #osm_ids = entity.get("osm").split(" ")
        #osm_types = entity.get("type").split(" ")
        #temp_key = '_'.join(osm_ids + osm_types)
        entity_geometry = geom.get_entity_geometry(entity)
        simplified_geometry = geom.simplify_geometry(entity_geometry, segments=2)
        entity_coordinates_list = []
        for polygon_list in simplified_geometry:
            coordinates = []
            for polygon in polygon_list:
                coordinates.append(geom.get_coordinates(polygon))
            entity_coordinates_list.append(coordinates)
        # print(entity_geometry)
        print(simplified_geometry)
        print(entity_coordinates_list)
        all_entity_coordinates[entity_id] = entity_coordinates_list
        print(entity_id)
    assert len(entities) == len(list(all_entity_coordinates.keys()))
    geom.close_connection()
    pickle_dump_large_file(all_entity_coordinates, args.output_dir_train)
