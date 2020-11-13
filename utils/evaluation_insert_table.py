from geometries import Geometries
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

with open('eval_preds_score.json', 'r') as file:
    output_raw = json.load(file)

entity2desc = pickle_load_large_file('../../geocode-data/collection_samples/model_input_desc_dev.pkl')
entityIds = list(entity2desc.keys())
for key, value in output_raw.items():
    for idx, prediction in enumerate(value):
        entity_id = entityIds[idx]
        geometry = geom.from_text("LINESTRING(%s)" % ", ".join([" ".join(map(str, point)) for e1, row in enumerate(prediction) for e2, point in enumerate(row) if not (e1 == 1 and e2 == 1)] + ["%s %s" % (prediction[0][0][0],prediction[0][0][1])]))


        geom.database.insert_in_table("output_table", idx, entity_id, geometry)