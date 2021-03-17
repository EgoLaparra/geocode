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



entity2target = pickle_load_large_file('/xdisk/bethard/zeyuzhang/Geo-Compositional_data/model_input_target_classification_bitmap_boundary_70_dev.pkl')
entityID2boundary = pickle_load_large_file('/xdisk/bethard/zeyuzhang/Geo-Compositional_data/model_input_boundary_classification_bitmap_boundary_70_dev.pkl')


num_table_inserted = 0
for idx,(entity_id, target_bitmap) in enumerate(entity2target.items()):
    min_bound, max_bound = entityID2boundary[entity_id]
    min_bound = (max(min_bound[0], -179.999999), max(min_bound[1], -89.999999))
    max_bound = (min(max_bound[0], 179.999999), min(max_bound[1], 89.999999))
    grid = bounded_grid(geom, 70, min_bound, max_bound)
    print("entity_id: ", entity_id)

    temp_flag = 0
    over_flag = []
    for each_row in target_bitmap:
        for item in each_row:
            if item > target_bitmap:
                temp_flag = 1
    if temp_flag == 0:
        continue
    # if 0 not in over_flag:
    #    continue
    num_table_inserted += 1
    print(entity_id)

    target_geometry = bitmap_to_geometry(geom, grid, target_bitmap)
    #print(prediction_values)
    #prediction_values = [[[prediction_values[0] - 26 / 2, prediction_values[1] - 26 / 2], [prediction_values[0] - 26 / 2, prediction_values[1] + 26 / 2]], [[prediction_values[0] + 26 / 2, prediction_values[1] + 26 / 2], [prediction_values[0] + 26 / 2, prediction_values[1] - 26 / 2]]]
    # print(prediction_values)
    # for e1, row in enumerate(prediction_values):
    #     for e2, point in enumerate(row):
    #         print(point)
    #         print(" ".join(map(str, point)))
    #geometry = geom.from_text("POLYGON((%s))" % ", ".join([" ".join(map(str, point)) for e1, row in enumerate(prediction_values) for e2, point in enumerate(row)] + ["%s %s" % (prediction_values[0][0][0],prediction_values[0][0][1])]))

    geom.database.insert_in_table("output_table", idx, entity_id, target_geometry)
print(num_table_inserted)

# for key, value in output_raw.items():
#     for idx, prediction in enumerate(value):
#         entity_id = entityIds[idx]
#         geometry = geom.from_text("LINESTRING(%s)" % ", ".join([" ".join(map(str, point)) for e1, row in enumerate(prediction) for e2, point in enumerate(row) if not (e1 == 1 and e2 == 1)] + ["%s %s" % (prediction[0][0][0],prediction[0][0][1])]))
#
#
#         geom.database.insert_in_table("output_table", idx, entity_id, geometry)