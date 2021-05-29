from itertools import chain
import spacy
import re


def get_text(node):
    parts = ([node.text] + list(chain(*(get_text(c) for c in node.getchildren()))) + [node.tail])
    return ''.join(filter(None, parts))


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
    nlp = spacy.blank("en")
    nlp.add_pipe("sentencizer")
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
