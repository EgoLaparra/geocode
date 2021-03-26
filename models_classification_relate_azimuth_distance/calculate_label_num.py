import os
import sys
import pickle

def pickle_load_large_file(filepath):
    max_bytes = 2 ** 31 - 1
    input_size = os.path.getsize(filepath)
    bytes_in = bytearray(0)
    with open(filepath, 'rb') as f_in:
        for _ in range(0, input_size, max_bytes):
            bytes_in += f_in.read(max_bytes)
    obj = pickle.loads(bytes_in)
    return obj

target_relate_train = pickle_load_large_file('/home/zeyuzhang/PycharmProjects/Geo_Compositional/geocode-data/collection_samples/model_input_target_relate_train.pkl')
target_relate_dev = pickle_load_large_file('/home/zeyuzhang/PycharmProjects/Geo_Compositional/geocode-data/collection_samples/model_input_target_relate_dev.pkl')

all_train_labels = []
for entity_id in target_relate_train.keys():
    all_train_labels.append(target_relate_train[entity_id])

all_dev_labels = []
for entity_id in target_relate_dev.keys():
    all_dev_labels.append(target_relate_dev[entity_id])
temp = []
for item in all_dev_labels:
    if item not in all_train_labels:
        temp.append(item)
print(temp)