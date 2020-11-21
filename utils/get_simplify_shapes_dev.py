from geometries import Geometries
from lxml import etree
from tqdm import tqdm
from itertools import chain
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
    print('node.text: ', node.text)
    print('node.tail: ', node.tail)
    #print(node.text.split(' '))
    #print(node.text.isspace())
    #print(node.tail.split(' '))
    #print(node.tail.isspace())
    #if node.text=='\n' and node.tail=='\n':
    #    print('True')
    parts = ([node.text] + list(chain(*(get_text(c) for c in node.getchildren()))) + [node.tail])
    #parts = (['Location'] + list(chain(*(get_text(c) for c in node.getchildren()))) + [node.tail])
    return ''.join(filter(None, parts))

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--xml_filepath_dev', default='../../geocode-data/collection_samples/dev_samples.xml', type=str,
                        help='path of data collections')
    parser.add_argument('--sample_size', default=50, type=int,
                        help='number of sample datas')
    parser.add_argument('--output_target_dev', default='../../geocode-data/collection_samples/model_input_target_dev.pkl', type=str,
                        help='path of data collections samples')
    parser.add_argument('--output_paras_dev', default='../../geocode-data/collection_samples/model_input_paras_dev.pkl',
                        type=str,
                        help='path of data collections samples')
    parser.add_argument('--output_desc_dev',
                        default='../../geocode-data/collection_samples/model_input_desc_dev.pkl',
                        type=str,
                        help='path of data collections samples')
    args = parser.parse_args()
    geom = Geometries()

    entities = get_entities_fromXML(args.xml_filepath_dev)
    print("entity numbers: ", len(entities))
    entityID2target = {}
    entityID2paras = {}
    entityID2desc = {}
    for entity in tqdm(entities, desc='Entities'):
        entity_id = entity.get("id")
        print(entity_id)
        try:
            # process paras entities
            pID2links = {}
            for p in entity.xpath('./p'):
                pID = p.get("id")
                #print('pid: ', pID)
                linkID2coordinates = {}
                for e, link in enumerate(p.xpath('./link')):
                    linkID = link.get("id")
                    #print('Link ID: ', linkID)
                    print('link.text: ', link.text)
                    link_geometry = geom.get_entity_geometry(link)
                    #print(geom.geometry_isempty(link_geometry))
                    #print(geom.get_geometry_area(link_geometry))
                    simplified_link_geometry = geom.simplify_geometry(link_geometry, segments=2)
                    link_coordinates_list = []
                    for polygon_list in simplified_link_geometry:
                        coordinates = []
                        for polygon in polygon_list:
                            coordinates.append(geom.get_coordinates(polygon))
                        link_coordinates_list.append(coordinates)
                    linkID2coordinates[linkID] = link_coordinates_list
                pID2links[pID] = linkID2coordinates
            ##process target entity
            #print('entityID: ', entity_id)
            entity_geometry = geom.get_entity_geometry(entity)
            simplified_geometry = geom.simplify_geometry(entity_geometry, segments=2)
            entity_coordinates_list = []
            for polygon_list in simplified_geometry:
                coordinates = []
                for polygon in polygon_list:
                    coordinates.append(geom.get_coordinates(polygon))
                entity_coordinates_list.append(coordinates)
            # print(entity_geometry)
            # print(simplified_geometry)
            # print(entity_coordinates_list)
            entityID2target[entity_id] = entity_coordinates_list
            ##process entity description
            temp_text = " ".join(entity.xpath('./p/text()'))
            print('temp_text: ', temp_text)
            text = get_text(entity)
            print('text: ', text)
            # print(text)
            entityID2desc[entity_id] = text
            entityID2paras[entity_id] = pID2links
        except Exception as e:
            print("Error processing %s" % (entity_id))
            print(e)
            geom = Geometries()
    print(len(list(entityID2desc.keys())))
    print(len(list(entityID2target.keys())))
    print(len(list(entityID2paras.keys())))
    #assert len(list(entityID2desc.keys())) == len(list(entityID2target.keys())) == len(list(entityID2paras.keys()))
    geom.close_connection()
    pickle_dump_large_file(entityID2target, args.output_target_dev)
    pickle_dump_large_file(entityID2paras, args.output_paras_dev)
    pickle_dump_large_file(entityID2desc, args.output_desc_dev)
