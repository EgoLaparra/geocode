from geometries import Geometries
from preprocess import coord_to_index_relative, geometry_group_bounds, geometry_to_bitmap, bitmap_to_geometry, limit_to_inner_boundaries, bounded_grid
from collections import OrderedDict
import spatial_relate as sprel
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

def get_text(node, e_id, flag):
    if not node.text.isspace() and not node.tail.isspace():
        if flag == e_id:
            node.text = 'LOCATION'
        flag+=1
    parts = ([node.text] + list(chain(*(get_text(c, e_id, flag) for c in node.getchildren()))) + [node.tail])

    return ''.join(filter(None, parts))

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--xml_filepath_dev', default='../../geocode-data/collection_samples/dev_samples.xml', type=str,
                        help='path of data collections')
    parser.add_argument('--sample_size', default=50, type=int,
                        help='number of sample datas')
    parser.add_argument('--output_relate_dev', default='/xdisk/bethard/zeyuzhang/Geo-Compositional_data/geocode-data/collection_samples/model_input_target_relate_dev.pkl', type=str,
                        help='path of data collections samples')
    parser.add_argument('--output_azimuth_dev', default='/xdisk/bethard/zeyuzhang/Geo-Compositional_data/geocode-data/collection_samples/model_input_target_azimuth_dev.pkl',
                        type=str,
                        help='path of data collections samples')
    parser.add_argument('--output_distance_dev',
                        default='/xdisk/bethard/zeyuzhang/Geo-Compositional_data/geocode-data/collection_samples/model_input_target_distance_dev.pkl',
                        type=str,
                        help='path of data collections samples')
    parser.add_argument('--output_desc_dev',
                        default='/xdisk/bethard/zeyuzhang/Geo-Compositional_data/geocode-data/collection_samples/model_input_desc_dev.pkl',
                        type=str,
                        help='path of data collections samples')
    parser.add_argument('--polygon_size',
                        default=10,
                        type=int,
                        help="polygon size of coor_2_index")

    args = parser.parse_args()
    geom = Geometries()

    entities = get_entities_fromXML(args.xml_filepath_dev)
    num_entities = len(entities)
    print("entity numbers: ", num_entities)
    linkID2desc = OrderedDict()
    linkID2relate = OrderedDict()
    linkID2azimuth = OrderedDict()
    linkID2distance = OrderedDict()
    entities = iter(entities)

    with tqdm(total=num_entities, desc='Entities') as progress_bar:
        entity = next(entities, None)
        while entity is not None:
            entity_id = entity.get("id")
            print(entity_id)
            try:
                ##process target entity
                entity_geometry = geom.get_entity_geometry(entity)
                #entity_type = geom.get_geometry_type(entity_geometry)
                #entity_size = sprel.geometry_size(geom, entity_geometry, entity_type)
                ##process paras entities
                for p in entity.xpath('./p'):
                    pID = p.get("id")
                    for e_id, link in enumerate(p.xpath('./link')):
                        linkID = link.get("id")
                        print("linkID: ", linkID)
                        geometry = geom.get_entity_geometry(link)
                        relate_matrix = geom.relate(entity_geometry, geometry)
                        reference_azimuth = sprel.reference_azimuth(geom, entity_geometry, geometry)
                        reference_distance = sprel.reference_distance(geom, entity_geometry, geometry)
                        flag=0
                        print("e_id: ", e_id)
                        text = get_text(entity, e_id, flag)
                        print("text: ", text)
                        linkID2relate[linkID] = relate_matrix
                        linkID2azimuth[linkID] = reference_azimuth
                        linkID2distance[linkID] = reference_distance
                        linkID2desc[linkID] = text


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

    print(len(list(linkID2relate.keys())))
    print(len(list(linkID2azimuth.keys())))
    print(len(list(linkID2distance.keys())))
    print(len(list(linkID2desc.keys())))
    assert len(list(linkID2relate.keys())) == len(list(linkID2azimuth.keys())) == len(list(linkID2distance.keys())) == len(list(linkID2desc.keys()))
    pickle_dump_large_file(linkID2relate, args.output_relate_dev)
    pickle_dump_large_file(linkID2azimuth, args.output_azimuth_dev)
    pickle_dump_large_file(linkID2distance, args.output_distance_dev)
    pickle_dump_large_file(linkID2desc, args.output_desc_dev)
    geom.close_connection()