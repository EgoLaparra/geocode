from geometries import Geometries
from preprocess import index_to_tile_relative, make_polygon, bitmap_to_geometry, bounded_grid
from lxml import etree
from tqdm import tqdm
from itertools import chain
import argparse
import pickle
import json
import sys
import os

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

with open('classification_bitmap_unet_results/eval_preds_26_6_epoch100.json', 'r') as file:
    output_raw = json.load(file)

entity2desc = pickle_load_large_file('/xdisk/bethard/zeyuzhang/Geo-Compositional_data/model_input_desc_classification_bitmap_26_dev.pkl')
entityID2boundary = pickle_load_large_file('/xdisk/bethard/zeyuzhang/Geo-Compositional_data/model_input_boundary_classification_bitmap_26_dev.pkl')
entityIds = list(entity2desc.keys())
print(output_raw.keys())
#value = output_raw['preds_Compositional_classification_relative_boundary/output_10_large']
value = output_raw['preds_output_bitmap_26_6_epoch100']
#print(value)
print(len(value))
threshold = .15
#0.06
for idx, prediction in enumerate(value):
    entity_id = entityIds[idx]
    min_bound, max_bound = entityID2boundary[entity_id]
    min_bound = (max(min_bound[0], -179.999999), max(min_bound[1], -89.999999))
    max_bound = (min(max_bound[0], 179.999999), min(max_bound[1], 89.999999))
    grid = bounded_grid(geom, 26, min_bound, max_bound)
    temp_flag = 0
    for each_row in prediction:
        for item in each_row:
            if item > threshold:
                temp_flag = 1
    if temp_flag == 0:
        continue
    print(idx)
    if idx == 'GL049_208':
        print(prediction)
    target_geometry = bitmap_to_geometry(geom, grid, prediction, threshold=threshold)
    #print(prediction_values)
    #prediction_values = [[[prediction_values[0] - 26 / 2, prediction_values[1] - 26 / 2], [prediction_values[0] - 26 / 2, prediction_values[1] + 26 / 2]], [[prediction_values[0] + 26 / 2, prediction_values[1] + 26 / 2], [prediction_values[0] + 26 / 2, prediction_values[1] - 26 / 2]]]
    # print(prediction_values)
    # for e1, row in enumerate(prediction_values):
    #     for e2, point in enumerate(row):
    #         print(point)
    #         print(" ".join(map(str, point)))
    #geometry = geom.from_text("POLYGON((%s))" % ", ".join([" ".join(map(str, point)) for e1, row in enumerate(prediction_values) for e2, point in enumerate(row)] + ["%s %s" % (prediction_values[0][0][0],prediction_values[0][0][1])]))

    geom.database.insert_in_table("output_table", idx, entity_id, target_geometry)


# for key, value in output_raw.items():
#     for idx, prediction in enumerate(value):
#         entity_id = entityIds[idx]
#         geometry = geom.from_text("LINESTRING(%s)" % ", ".join([" ".join(map(str, point)) for e1, row in enumerate(prediction) for e2, point in enumerate(row) if not (e1 == 1 and e2 == 1)] + ["%s %s" % (prediction[0][0][0],prediction[0][0][1])]))
#
#
#         geom.database.insert_in_table("output_table", idx, entity_id, geometry)