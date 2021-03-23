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

geom = Geometries()

with open('/xdisk/bethard/zeyuzhang/Geo-Compositional_classification_bitmap_unet_deeper/output_64_6_large_epoch300/eval_preds.json', 'r') as file:
    output_raw = json.load(file)

entity2desc = pickle_load_large_file('/xdisk/bethard/zeyuzhang/Geo-Compositional_data/model_input_desc_classification_bitmap_boundary_64_dev.pkl')
entityID2boundary = pickle_load_large_file('/xdisk/bethard/zeyuzhang/Geo-Compositional_data/model_input_boundary_classification_bitmap_boundary_64_dev.pkl')
entityIds = list(entity2desc.keys())
print(output_raw.keys())
#value = output_raw['preds_Compositional_classification_relative_boundary/output_10_large']
value = output_raw['preds_Compositional_classification_bitmap_unet_deeper/output_64_6_large_epoch300']
#print(value)
print(len(value))
threshold = .3
#0.06
num_table_inserted = 0
for idx, prediction in enumerate(value):
    entity_id = entityIds[idx]
    min_bound, max_bound = entityID2boundary[entity_id]
    min_bound = (max(min_bound[0], -179.999999), max(min_bound[1], -89.999999))
    max_bound = (min(max_bound[0], 179.999999), min(max_bound[1], 89.999999))
    grid = bounded_grid(geom, 64, min_bound, max_bound)
    temp_flag = 0
    for each_row in prediction:
        for item in each_row:
            if item > threshold:
                temp_flag = 1
    #if entity_id == 'GL033_200':
    #    pickle_dump_large_file(grid, "./debug_grid.pkl")
    #    pickle_dump_large_file(prediction, "./debug_bitmap.pkl")
    #    continue

    if temp_flag == 0:
        continue

    num_table_inserted+=1
    print(entity_id)
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

print(num_table_inserted)
# for key, value in output_raw.items():
#     for idx, prediction in enumerate(value):
#         entity_id = entityIds[idx]
#         geometry = geom.from_text("LINESTRING(%s)" % ", ".join([" ".join(map(str, point)) for e1, row in enumerate(prediction) for e2, point in enumerate(row) if not (e1 == 1 and e2 == 1)] + ["%s %s" % (prediction[0][0][0],prediction[0][0][1])]))
#
#
#         geom.database.insert_in_table("output_table", idx, entity_id, geometry)