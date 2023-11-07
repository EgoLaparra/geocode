from itertools import chain
from functools import reduce
import spacy
import re


def get_text_from_parts(parts):
    return "".join([part[1] for part in parts])


def get_text(node):
    parts = get_parts(node)
    return get_text_from_parts(parts)


def get_parts(node):
    parts = [[node, node.text]] + list(chain(*(get_parts(c) for c in node.getchildren()))) + [[None, node.tail]]
    return filter(lambda x: x[1] is not None, parts)


def get_links(node):
    parts = reduce(lambda x, y: x + [[y[0], x[-1][-1], x[-1][-1] + len(y[1])]], get_parts(node), [[None, 0, 0]])
    return filter(lambda x: x[0] is not None and x[0].tag == "link", parts)


def get_recursive_partial_text(node, until):
    parts = [node.text]
    if node == until:
        return True, ''.join(filter(None, parts))
    for child in node.getchildren():
        found, child_part = get_recursive_partial_text(child, until)
        parts.append(child_part)
        if found:
            return True, ''.join(filter(None, parts))
    parts.append(node.tail)
    return False, ''.join(filter(None, parts))


def get_partial_text(node, until):
    found, partial_text = get_recursive_partial_text(node, until)
    return partial_text if found else None


def init_nlp():
    nlp = spacy.load("en_core_web_sm")
    return nlp


def split_description(nlp, entity):
    splits = []
    for link in entity.xpath('.//link'):
        link_text_copy = link.text
        link.text = "LOCATION"
        partial_text = get_partial_text(entity, link)
        partial_text = re.sub(r'\[([0-9]+|citation needed)\]', '', partial_text)
        doc = nlp(partial_text)
        sents = iter(reversed(list(doc.sents)))
        link_sentence = None
        while link_sentence is None:
            sent = next(sents)
            sent = sent.text.strip().replace("\xa0", " ")
            link_sentence = sent if sent != "" else None
        splits.append(link_sentence)
        link.text = link_text_copy
    return splits
