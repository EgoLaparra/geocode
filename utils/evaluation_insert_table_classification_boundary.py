from geometries import Geometries
from preprocess import index_to_tile_relative, make_polygon
from lxml import etree
from tqdm import tqdm
from itertools import chain
import argparse
import pickle
import json
import sys
import os

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
    prediction_values = [[[y, x], [y, x - polygon_size]], [[y + polygon_size, x - polygon_size], [y + polygon_size, x]]]
    return prediction_values

def pickle_load_large_file(filepath):
    max_bytes = 2**31 - 1
    input_size = os.path.getsize(filepath)
    bytes_in = bytearray(0)
    with open(filepath, 'rb') as f_in:
        for _ in range(0, input_size, max_bytes):
            bytes_in += f_in.read(max_bytes)
    obj = pickle.loads(bytes_in)
    return obj

geom = Geometries()

with open('classification_relative_boundary_results/eval_preds_26_epoch50.json', 'r') as file:
    output_raw = json.load(file)

entity2desc = pickle_load_large_file('../../geocode-data/collection_samples/model_input_desc_dev.pkl')
entityID2boundary = pickle_load_large_file('../../geocode-data/collection_samples/model_input_boundary_classification_relative_boundary_26_dev.pkl')
entityIds = list(entity2desc.keys())
print(output_raw.keys())
value = output_raw['preds_Compositional_classification_relative_boundary/output_26_epoch50']
#print(value)
print(len(value))


for idx, prediction in enumerate(value):
    entity_id = entityIds[idx]
    min_bound, max_bound = entityID2boundary[entity_id]
    prediction_values = index_to_tile_relative(prediction, 26, min_bound, max_bound)
    print(prediction_values)
    geometry = make_polygon(geom, prediction_values)
    #print(prediction_values)
    #prediction_values = [[[prediction_values[0] - 26 / 2, prediction_values[1] - 26 / 2], [prediction_values[0] - 26 / 2, prediction_values[1] + 26 / 2]], [[prediction_values[0] + 26 / 2, prediction_values[1] + 26 / 2], [prediction_values[0] + 26 / 2, prediction_values[1] - 26 / 2]]]
    # print(prediction_values)
    # for e1, row in enumerate(prediction_values):
    #     for e2, point in enumerate(row):
    #         print(point)
    #         print(" ".join(map(str, point)))
    #geometry = geom.from_text("POLYGON((%s))" % ", ".join([" ".join(map(str, point)) for e1, row in enumerate(prediction_values) for e2, point in enumerate(row)] + ["%s %s" % (prediction_values[0][0][0],prediction_values[0][0][1])]))

    geom.database.insert_in_table("output_table", idx, entity_id, geometry)


# for key, value in output_raw.items():
#     for idx, prediction in enumerate(value):
#         entity_id = entityIds[idx]
#         geometry = geom.from_text("LINESTRING(%s)" % ", ".join([" ".join(map(str, point)) for e1, row in enumerate(prediction) for e2, point in enumerate(row) if not (e1 == 1 and e2 == 1)] + ["%s %s" % (prediction[0][0][0],prediction[0][0][1])]))
#
#
#         geom.database.insert_in_table("output_table", idx, entity_id, geometry)