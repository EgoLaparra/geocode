import re
import sys
from lxml import etree

import text_preprocess as tp


def prepare_text(entity, pol_colors, nlp):
    general_id = entity.get("id")
    links_raw = tp.get_links(entity)

    # TODO: can be put into one line
    links = [(link[0].text, '_'.join(link[0].get("osm").split())) for link in links_raw]


    colors_map = {link: f"OSM{link_id}" for link, link_id in links}
    parts = list(tp.get_parts(entity))

    for part in parts:
        if part[0] is not None and part[0].tag == "link" and part[1] in colors_map:
            part[1] = colors_map[part[1]]

    text = tp.get_text_from_parts(parts).strip()

    links_text = [text for text, _ in links]
    for link in sorted(links_text, key=lambda x: -len(x)):
        if link in colors_map:
            text = text.replace(link, colors_map[link])

    doc = nlp(text)
    verbs = [e for e, t in enumerate(doc) if t.pos_ in ("AUX", "VERB") and t.lemma_ != "call"]
    if len(verbs) > 0 and verbs[0] > 0:
        text = "TARGET %s" % doc[verbs[0]:]

    cleaned_text = " ".join(text.split()) # remove extra white spaces
    return  f"{general_id}\t{cleaned_text}"


nlp = tp.init_nlp()
pol_colors = ["red", "lime", "blue", "yellow", "magenta", "cyan"]
data = etree.parse(sys.argv[1])
for entity in data.xpath("//entity"):
    print(prepare_text(entity, pol_colors, nlp))
