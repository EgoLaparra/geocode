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

def coord_to_index(coordinates, polygon_size):
    """
    Convert coordinates into an array (world representation) index. Use that to modify map_vector polygon value.
    :param coordinates: (latitude, longitude) to convert to the map vector index
    :param polygon_size: integer size of the polygon? i.e. the resolution of the world
    :return: index pointing into map_vector array
    """
    latitude = float(coordinates[0]) - 90 if float(coordinates[0]) != -90 else -179.99  # The two edge cases must
    longitude = float(coordinates[1]) + 180 if float(coordinates[1]) != 180 else 359.99  # get handled differently!
    if longitude < 0:
        longitude = -longitude
    if latitude < 0:
        latitude = -latitude
    x = int(360 / polygon_size) * int(latitude / polygon_size)
    y = int(longitude / polygon_size)
    return x + y if 0 <= x + y <= int(360 / polygon_size) * int(180 / polygon_size) else Exception(u"Shock horror!!")


def index_to_coord(index, polygon_size):
    """
    Convert index (output of the prediction model) back to coordinates.
    :param index: of the polygon/tile in map_vector array (given by model prediction)
    :param polygon_size: size of each polygon/tile i.e. resolution of the world
    :return: pair of (latitude, longitude)
    """
    x = int(index / (360 / polygon_size))
    y = index % int(360 / polygon_size)
    if x > int(90 / polygon_size):
        x = -int((x - (90 / polygon_size)) * polygon_size)
    else:
        x = int(((90 / polygon_size) - x) * polygon_size)
    if y < int(180 / polygon_size):
        y = -int(((180 / polygon_size) - y) * polygon_size)
    else:
        y = int((y - (180 / polygon_size)) * polygon_size)
    return x, y

def get_entities_fromXML(xml_filepath):
    collection = etree.parse(xml_filepath)
    all_entities = collection.xpath('//entity')

    return all_entities

def get_text(node):
    # if not node.text.isspace() and not node.tail.isspace():
    #     node.text = 'LOCATION'
    parts = ([node.text] + list(chain(*(get_text(c) for c in node.getchildren()))) + [node.tail])

    return ''.join(filter(None, parts))

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--xml_filepath_train', default='../../geocode-data/collection_samples/train_samples.xml', type=str,
                        help='path of data collections')
    parser.add_argument('--sample_size', default=50, type=int,
                        help='number of sample datas')
    parser.add_argument('--output_target_train', default='../../geocode-data/collection_samples/model_input_target_classification_train.pkl', type=str,
                        help='path of data collections samples')
    parser.add_argument('--output_paras_train', default='../../geocode-data/collection_samples/model_input_paras_classification_train.pkl',
                        type=str,
                        help='path of data collections samples')
    parser.add_argument('--output_desc_train',
                        default='../../geocode-data/collection_samples/model_input_desc_classification_train.pkl',
                        type=str,
                        help='path of data collections samples')
    args = parser.parse_args()
    geom = Geometries()

    entities = get_entities_fromXML(args.xml_filepath_train)
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
                linkID2coordinates = {}
                for e, link in enumerate(p.xpath('./link')):
                    linkID = link.get("id")
                    link_geometry = geom.get_entity_geometry(link)
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

            entity_geometry = geom.get_entity_geometry(entity)
            entity_central_point = geom.get_centrality(entity_geometry, metric="centroid")
            entity_central_coordinates = geom.get_coordinates(entity_central_point)
            print('entity central point: ', entity_central_coordinates)
            entity_classification_label = coord_to_index(entity_central_coordinates, 10)
            print('classification_label: ', entity_classification_label)
            entityID2target[entity_id] = entity_classification_label
            # simplified_geometry = geom.simplify_geometry(entity_geometry, segments=2)
            # entity_coordinates_list = []
            # for polygon_list in simplified_geometry:
            #     coordinates = []
            #     for polygon in polygon_list:
            #         coordinates.append(geom.get_coordinates(polygon))
            #     entity_coordinates_list.append(coordinates)
            # entityID2target[entity_id] = entity_coordinates_list


            ##process entity description
            # temp_text = " ".join(entity.xpath('./p/text()'))
            # print('temp_text: ', temp_text)
            # text = get_text(entity)
            # print('text: ', text)
            # entityID2desc[entity_id] = text
            # entityID2paras[entity_id] = pID2links
        except Exception as e:
            print("Error processing %s" % (entity_id))
            print(e)
            geom = Geometries()
    # print(len(list(entityID2desc.keys())))
    print(len(list(entityID2target.keys())))
    # print(len(list(entityID2paras.keys())))
    # assert len(list(entityID2desc.keys())) == len(list(entityID2target.keys())) == len(list(entityID2paras.keys()))
    geom.close_connection()
    pickle_dump_large_file(entityID2target, args.output_target_train)
    # pickle_dump_large_file(entityID2paras, args.output_paras_train)
    # pickle_dump_large_file(entityID2desc, args.output_desc_train)
