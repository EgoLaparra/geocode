from geometries import Geometries
from preprocess import coord_to_index_relative, geometry_group_bounds, geometry_to_bitmap, bitmap_to_geometry, limit_to_inner_boundaries, bounded_grid
from collections import OrderedDict
from lxml import etree
from tqdm import tqdm
from itertools import chain
from time import sleep
from psycopg2 import OperationalError
import argparse
import pickle
import sys
import os
import traceback

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
    parser.add_argument('--output_target_dev', default='../../geocode-data/collection_samples/model_input_target_classification_bitmap_boundary_70_dev.pkl', type=str,
                        help='path of data collections samples')
    parser.add_argument('--output_paras_dev', default='../../geocode-data/collection_samples/model_input_paras_classification_bitmap_boundary_70_dev.pkl',
                        type=str,
                        help='path of data collections samples')
    parser.add_argument('--output_desc_dev',
                        default='../../geocode-data/collection_samples/model_input_desc_classification_bitmap_boundary_70_dev.pkl',
                        type=str,
                        help='path of data collections samples')
    parser.add_argument('--output_boundary_dev',
                        default='../../geocode-data/collection_samples/model_input_boundary_classification_bitmap_boundary_70_dev.pkl',
                        type=str,
                        help='path of data collections samples')
    parser.add_argument('--polygon_size',
                        default=70,
                        type=int,
                        help="polygon size of coor_2_index")
    args = parser.parse_args()
    geom = Geometries()

    entities = get_entities_fromXML(args.xml_filepath_dev)
    num_entities = len(entities)
    print("entity numbers: ", num_entities)
    entityID2target = {}
    entityID2paras = {}
    entityID2desc = {}
    entityID2boundary = {}
    entities = iter(entities)
    with tqdm(total=num_entities, desc='Entities') as progress_bar:
        entity = next(entities, None)
        while entity is not None:
            entity_id = entity.get("id")
            print(entity_id)
            geometries = []
            try:
                # process paras entities
                for p in entity.xpath('./p'):
                    for e, link in enumerate(p.xpath('./link')):
                        link_geometry = geom.get_entity_geometry(link)
                        geometries.append(link_geometry)

                limit_to_inner_boundaries(geom, geometries)
                min_bound, max_bound = geometry_group_bounds(geom, geometries, squared=True)
                min_bound = (max(min_bound[0], -179.999999), max(min_bound[1], -89.999999))
                max_bound = (min(max_bound[0], 179.999999), min(max_bound[1], 89.999999))
                grid = bounded_grid(geom, args.polygon_size, min_bound, max_bound)
                geometries = iter(geometries)
                pID2links = OrderedDict()
                for p in entity.xpath('./p'):
                    pID = p.get("id")
                    linkID2coordinates = OrderedDict()
                    for e, link in enumerate(p.xpath('./link')):
                        linkID = link.get("id")
                        link_geometry = next(geometries)
                        link_bitmap = geometry_to_bitmap(geom, grid, link_geometry)
                        # link_geometry_from_bitmap = bitmap_to_geometry(geom, grid, link_bitmap)
                        linkID2coordinates[linkID] = link_bitmap
                    pID2links[pID] = linkID2coordinates

                ##process target entity
                entity_geometry = geom.get_entity_geometry(entity)
                entity_points = geom.dump_points(geom.get_envelope(entity_geometry))
                entity_min = geom.get_coordinates(entity_points[0])
                entity_max = geom.get_coordinates(entity_points[2])
                if entity_max[0] < min_bound[0] or entity_max[1] < min_bound[1] or entity_min[0] > max_bound[0] or entity_min[1] > max_bound[1]:
                    raise Exception("OUT_OF_BOUNDS!")
                target_bitmap = geometry_to_bitmap(geom, grid, entity_geometry)
                # target_geometry_from_bitmap = bitmap_to_geometry(geom, grid, target_bitmap)
                print('target_geometry_from_bitmap: ', target_bitmap)
                print(len(target_bitmap))
                # print('length', len(target_geometry_from_bitmap))

                ##process entity description
                # temp_text = " ".join(entity.xpath('./p/text()'))
                # print('temp_text: ', temp_text)
                text = get_text(entity)
                print('text: ', text)
                entityID2desc[entity_id] = text
                entityID2paras[entity_id] = pID2links
                entityID2target[entity_id] = target_bitmap
                entityID2boundary[entity_id] = [min_bound, max_bound]
                progress_bar.update(1)
                entity = next(entities, None)
            except OperationalError as e:
                print("OperationalError processing %s" % (entity_id))
                print(e)
                traceback.print_exc(file=sys.stdout)
                while geom.database.conn.closed:
                    try:
                        sleep(5)
                        geom = Geometries()
                    except:
                        pass
            except Exception as e:
                print("Error processing %s" % (entity_id))
                print(e)
                traceback.print_exc(file=sys.stdout)
                progress_bar.update(1)
                entity = next(entities, None)
                geom = Geometries()

    print(len(list(entityID2desc.keys())))
    print(len(list(entityID2target.keys())))
    print(len(list(entityID2paras.keys())))
    assert len(list(entityID2desc.keys())) == len(list(entityID2target.keys())) == len(list(entityID2paras.keys()))
    pickle_dump_large_file(entityID2target, args.output_target_dev)
    pickle_dump_large_file(entityID2paras, args.output_paras_dev)
    pickle_dump_large_file(entityID2desc, args.output_desc_dev)
    pickle_dump_large_file(entityID2boundary, args.output_boundary_dev)
    geom.close_connection()
