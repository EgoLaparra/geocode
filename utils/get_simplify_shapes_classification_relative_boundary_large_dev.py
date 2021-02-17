from geometries import Geometries
from preprocess import coord_to_index_relative, geometry_group_bounds, limit_to_inner_boundaries
from lxml import etree
from tqdm import tqdm
from itertools import chain
from collections import OrderedDict
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

def get_text(node):
    #if not node.text.isspace() and not node.tail.isspace():
    #    node.text = 'LOCATION'
    parts = ([node.text] + list(chain(*(get_text(c) for c in node.getchildren()))) + [node.tail])

    return ''.join(filter(None, parts))

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--xml_filepath_dev', default='../../geocode-data/collection_samples/dev_samples.xml', type=str,
                        help='path of data collections')
    parser.add_argument('--sample_size', default=50, type=int,
                        help='number of sample datas')
    parser.add_argument('--output_target_dev', default='../../geocode-data/collection_samples/model_input_target_classification_relative_boundary_10_dev.pkl', type=str,
                        help='path of data collections samples')
    parser.add_argument('--output_paras_dev', default='../../geocode-data/collection_samples/model_input_paras_classification_relative_boundary_10_dev.pkl',
                        type=str,
                        help='path of data collections samples')
    parser.add_argument('--output_desc_dev',
                        default='../../geocode-data/collection_samples/model_input_desc_classification_relative_boundary_10_dev.pkl',
                        type=str,
                        help='path of data collections samples')
    parser.add_argument('--output_boundary_dev',
                        default='../../geocode-data/collection_samples/model_input_boundary_classification_relative_boundary_10_dev.pkl',
                        type=str,
                        help='path of data collections samples')
    parser.add_argument('--polygon_size',
                        default=10,
                        type=int,
                        help="polygon size of coor_2_index")
    args = parser.parse_args()
    geom = Geometries()

    entities = get_entities_fromXML(args.xml_filepath_dev)
    print("entity numbers: ", len(entities))
    entityID2target = {}
    entityID2paras = {}
    entityID2desc = {}
    entityID2boundary = {}
    for entity in tqdm(entities, desc='Entities'):
        entity_id = entity.get("id")
        print(entity_id)
        geometries = []
        try:
            ##process paras entities
            for p in entity.xpath('./p'):
                for e, link in enumerate(p.xpath('./link')):
                    link_geometry = geom.get_entity_geometry(link)
                    geometries.append(link_geometry)

            # limit_to_inner_boundaries(geom, geometries)
            min_bound, max_bound = geometry_group_bounds(geom, geometries, squared=True)
            min_bound = (max(min_bound[0], -179.999999), max(min_bound[1], -89.999999))
            max_bound = (min(max_bound[0], 179.999999), min(max_bound[1], 89.999999))
            pID2links = OrderedDict()
            for p in entity.xpath('./p'):
                pID = p.get("id")
                linkID2coordinates = OrderedDict()
                for e, link in enumerate(p.xpath('./link')):
                    linkID = link.get("id")
                    link_geometry = geom.get_entity_geometry(link)
                    link_central_point = geom.get_centrality(link_geometry, metric="centroid")
                    link_central_x, link_central_y = geom.get_coordinates(link_central_point)
                    link_classification_label = coord_to_index_relative((link_central_x, link_central_y),
                                                                        args.polygon_size, min_bound, max_bound)
                    linkID2coordinates[linkID] = link_classification_label
                pID2links[pID] = linkID2coordinates

            ##process target entity
            entity_geometry = geom.get_entity_geometry(entity)
            entity_central_point = geom.get_centrality(entity_geometry, metric="centroid")
            entity_central_x, entity_central_y = geom.get_coordinates(entity_central_point)
            print('entity central point: ', (entity_central_x, entity_central_y))
            entity_classification_label = coord_to_index_relative((entity_central_x, entity_central_y),
                                                                  args.polygon_size, min_bound, max_bound)
            print('classification_label: ', entity_classification_label)

            ##process entity description
            # temp_text = " ".join(entity.xpath('./p/text()'))
            # print('temp_text: ', temp_text)
            text = get_text(entity)
            print('text: ', text)
            entityID2desc[entity_id] = text
            entityID2paras[entity_id] = pID2links
            entityID2target[entity_id] = entity_classification_label
            entityID2boundary[entity_id] = [min_bound,max_bound]
        except Exception as e:
            print("Error processing %s" % (entity_id))
            print(e)
            geom = Geometries()
    print(len(list(entityID2desc.keys())))
    print(len(list(entityID2target.keys())))
    print(len(list(entityID2paras.keys())))
    assert len(list(entityID2desc.keys())) == len(list(entityID2target.keys())) == len(list(entityID2paras.keys()))
    geom.close_connection()
    pickle_dump_large_file(entityID2target, args.output_target_dev)
    pickle_dump_large_file(entityID2paras, args.output_paras_dev)
    pickle_dump_large_file(entityID2desc, args.output_desc_dev)
    pickle_dump_large_file(entityID2boundary, args.output_boundary_dev)
