# coding=utf-8
# Copyright 2018 The Google AI Language Team Authors and The HuggingFace Inc. team.
# Copyright (c) 2018, NVIDIA CORPORATION.  All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
""" Multiple choice fine-tuning: utilities to work with multiple choice tasks of reading comprehension  """


import csv
import re
import glob
import json
import types
import logging
import os
import pickle
import sys
import numpy as np
from typing import List

import tqdm

from transformers import PreTrainedTokenizer


logger = logging.getLogger(__name__)


class InputExample(object):
    """A single training/test example for multiple choice"""

    def __init__(self, example_id, text_a, text_b, para_links, label=None):
        """
    A single training/test example for simple sequence classification.
    Args:
        guid: Unique id for the example.
        text_a: string. The untokenized text of the first sequence. For single
        sequence tasks, only this sequence must be specified.
        text_b: (Optional) string. The untokenized text of the second sequence.
        Only must be specified for sequence pair tasks.
        label: (Optional) string. The label of the example. This should be
        specified for train and dev examples, but not for test examples.
    """
        self.example_id = example_id
        self.text_a= text_a
        self.text_b = text_b
        self.para_links = para_links
        self.label = label


class InputFeatures(object):
    def __init__(self, example_id, input_ids, attention_mask, token_type_ids, para_links, label):
        self.example_id = example_id
        self.input_ids = input_ids
        self.attention_mask = attention_mask
        self.token_type_ids = token_type_ids
        self.para_links = para_links
        self.label = label


class DataProcessor(object):
    """Base class for data converters for multiple choice data sets."""

    def get_train_examples(self, data_dir):
        """Gets a collection of `InputExample`s for the train set."""
        raise NotImplementedError()

    def get_dev_examples(self, data_dir):
        """Gets a collection of `InputExample`s for the dev set."""
        raise NotImplementedError()

    def get_test_examples(self, data_dir):
        """Gets a collection of `InputExample`s for the test set."""
        raise NotImplementedError()

    def get_labels(self):
        """Gets the list of labels for this data set."""
        raise NotImplementedError()

class GeoComposeProcessor(DataProcessor):
    """Processor for the Toponym data set."""

    def get_train_examples(self, data_dir):
        """See base class."""
        logger.info("LOOKING AT {} train".format(data_dir))
        return self._create_examples(self.pickle_load_large_file(os.path.join(data_dir, "model_input_desc_classification_relative_boundary_100_large_train.pkl")),
                                     self.pickle_load_large_file(os.path.join(data_dir, "model_input_paras_classification_relative_boundary_100_large_train.pkl")),
                                     self.pickle_load_large_file(os.path.join(data_dir, "model_input_target_classification_relative_boundary_100_large_train.pkl")),"train")

    def get_dev_examples(self, data_dir):
        """See base class."""
        logger.info("LOOKING AT {} dev".format(data_dir))
        return self._create_examples(self.pickle_load_large_file(os.path.join(data_dir, "model_input_desc_classification_relative_boundary_100_dev.pkl")),
                                     self.pickle_load_large_file(os.path.join(data_dir, "model_input_paras_classification_relative_boundary_100_dev.pkl")),
                                     self.pickle_load_large_file(os.path.join(data_dir, "model_input_target_classification_relative_boundary_100_dev.pkl")), "dev")

    def get_test_examples(self, data_dir):
        """See base class."""
        logger.info("LOOKING AT {} test".format(data_dir))
        return self._create_examples(self.pickle_load_large_file(os.path.join(data_dir, "model_input_desc_dev.pkl")),
                                     self.pickle_load_large_file(os.path.join(data_dir, "model_input_paras_dev.pkl")),
                                     self.pickle_load_large_file(os.path.join(data_dir, "model_input_target_dev.pkl")), "test")

    def get_labels(self, n_labels):
        """See base class."""
        self.n_labels = n_labels
        return [item for item in range(n_labels)]

    def pickle_dump_large_file(self, obj, filepath):
        max_bytes = 2 ** 31 - 1
        bytes_out = pickle.dumps(obj)
        n_bytes = sys.getsizeof(bytes_out)
        with open(filepath, 'wb') as f_out:
            for idx in range(0, n_bytes, max_bytes):
                f_out.write(bytes_out[idx:idx + max_bytes])

    def pickle_load_large_file(self, filepath):
        max_bytes = 2 ** 31 - 1
        input_size = os.path.getsize(filepath)
        bytes_in = bytearray(0)
        with open(filepath, 'rb') as f_in:
            for _ in range(0, input_size, max_bytes):
                bytes_in += f_in.read(max_bytes)
        obj = pickle.loads(bytes_in)
        return obj

    def _read_csv(self, input_file):
        with open(input_file, "r", encoding="utf-8") as f:
            reader = csv.reader(f, delimiter='\t')
            lines = []
            for line in reader:
                lines.append(line)
            return lines

    def _create_examples(self, desciptions, paras, targets, type: str):
        """Creates examples for the training and dev sets."""
        examples = []
        max_links_num = 0
        norm_bench = np.array([[[180, 90]]])
        print(len(list(desciptions.keys())))
        for entity_id in desciptions.keys():
            if entity_id not in paras.keys():
                continue
            para = paras[entity_id]
            para_entities = []
            for single_para in para.keys():
                for link_id in para[single_para].keys():
                    para_entities.append(para[single_para][link_id])
            if len(para_entities) > max_links_num:
                max_links_num = len(para_entities)
        print('max_links_num: ', max_links_num)
        for idx, entity_id in enumerate(list(desciptions.keys())):
            desciption = desciptions[entity_id]
            text = re.sub(r'( |\n|\t)+', ' ', desciption.strip())
            if entity_id not in paras.keys():
                continue
            para = paras[entity_id]
            if entity_id not in targets.keys():
                continue
            target = targets[entity_id]
            if not isinstance(target, int):
                target = 0
            para_entities = []
            for single_para in para.keys():
                for link_id in para[single_para].keys():
                    para_entities.append(para[single_para][link_id])
            para_entities_vector = np.eye(self.n_labels)[para_entities].tolist()
            if len(para_entities_vector) < max_links_num:
                para_entities_vector = para_entities_vector + [np.zeros(self.n_labels).tolist()] * (
                            max_links_num - len(para_entities_vector))
            assert len(para_entities_vector) == max_links_num
            examples.append(InputExample(
                example_id=str(idx),
                text_a=text,
                text_b="",
                para_links=para_entities_vector,
                label=target,
            ))
        print(len(examples))
        return examples



def convert_examples_to_features(
    examples: List[InputExample],
    label_list: List[str],
    max_length: int,
    tokenizer: PreTrainedTokenizer,
    pad_token_segment_id=0,
    pad_on_left=False,
    pad_token=0,
    mask_padding_with_zero=True,
) -> List[InputFeatures]:
    """
    Loads a data file into a list of `InputFeatures`
    """

    label_map = {label: i for i, label in enumerate(label_list)}

    features = []
    for (ex_index, example) in tqdm.tqdm(enumerate(examples), desc="convert examples to features"):
        if ex_index % 10000 == 0:
            logger.info("Writing example %d of %d" % (ex_index, len(examples)))
        inputs = tokenizer.encode_plus(example.text_a, example.text_b, add_special_tokens=True, max_length=max_length, )
        if "num_truncated_tokens" in inputs and inputs["num_truncated_tokens"] > 0:
            logger.info(
                "Attention! you are cropping tokens (swag task is ok). "
                "If you are training ARC and RACE and you are poping question + options,"
                "you need to try to use a bigger max seq length!"
            )

        input_ids, token_type_ids = inputs["input_ids"], inputs["token_type_ids"]
        # The mask has 1 for real tokens and 0 for padding tokens. Only real
        # tokens are attended to.
        attention_mask = [1 if mask_padding_with_zero else 0] * len(input_ids)

        # Zero-pad up to the sequence length.
        padding_length = max_length - len(input_ids)
        if pad_on_left:
            input_ids = ([pad_token] * padding_length) + input_ids
            attention_mask = ([0 if mask_padding_with_zero else 1] * padding_length) + attention_mask
            token_type_ids = ([pad_token_segment_id] * padding_length) + token_type_ids
        else:
            input_ids = input_ids + ([pad_token] * padding_length)
            attention_mask = attention_mask + ([0 if mask_padding_with_zero else 1] * padding_length)
            token_type_ids = token_type_ids + ([pad_token_segment_id] * padding_length)

        assert len(input_ids) == max_length
        assert len(attention_mask) == max_length
        assert len(token_type_ids) == max_length

        #label = label_map[example.label]

        if ex_index < 5:
            logger.info("*** Example ***")
            logger.info("guid: %s" % (example.example_id))
            logger.info("input_ids: %s" % " ".join([str(x) for x in input_ids]))
            logger.info("attention_mask: %s" % " ".join([str(x) for x in attention_mask]))
            logger.info("token_type_ids: %s" % " ".join([str(x) for x in token_type_ids]))
            #logger.info("label: %s (id = %d)" % (example.label, label))

        features.append(InputFeatures(example_id=example.example_id, input_ids=input_ids,
                attention_mask=attention_mask,
                token_type_ids=token_type_ids,
                para_links = example.para_links,
                label=example.label,))

    return features


processors = {"geocompose": GeoComposeProcessor}


MULTIPLE_CHOICE_TASKS_NUM_LABELS = {"geocompose", 1}
