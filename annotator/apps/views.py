from lxml import etree, html
import numpy as np
import os
from collections import OrderedDict

from django.shortcuts import render
from django import forms
from django.views.decorators.csrf import csrf_exempt


class OSM:
    def __init__(self, oid, otype):
        self.oid = oid
        self.otype = otype


class Paragraph:
    def __init__(self):
        self.id = None
        self.content = []
        self.children = []


class Text:
    def __init__(self, id, text, color):
        self.id = id
        self.text = text
        self.color = color


class Entity:
    def __init__(self, id, wikipedia):
        self.id = id
        self.wikipedia = wikipedia
        self.osm = []
        self.paragraphs = []
        self.color = None
        self.saved = None
        self.script = None


class Collection:
    def __init__(self, doc_list):
        self.doc_list = doc_list
        self.opened = None


def iterelem(elem, union, color):
    paragraph = Paragraph()
    if elem.text is not None:
        if color is not None:
            paragraph.content.append(Text(elem.get('id'), elem.text, color))
        else:
            paragraph.content.append(Text(None, elem.text, color))
    for child in elem.getchildren():
        r = str(np.random.randint(80, high=220))
        g = str(np.random.randint(80, high=220))
        b = str(np.random.randint(80, high=220))
        child_entity = Entity(child.get('id'), child.get('wikipedia'))
        child_entity.color = "%s,%s,%s" % (r, g, b)
        for osm, otype in zip(child.get('osm').split(' '), child.get('type').split(' ')):
            child_entity.osm.append(OSM(osm, otype))
            new_id = etree.SubElement(union, "id-query")
            new_id.set("type", otype)
            new_id.set("ref", osm)
        paragraph.children.append(child_entity)
        child_paragraph = iterelem(child, union, child_entity.color)
        paragraph.content.extend(child_paragraph.content)
    if elem.tail is not None:
        paragraph.content.append(Text(None, elem.tail, None))
    return paragraph


def index(request):
    entities = []
    doc_path = "./documents"
    doc_list = os.listdir(doc_path)
    collection = Collection(doc_list)
    if request.method == "POST":
        form = forms.Form(request.POST)
        collection.opened = form.data["file_name"]
    if collection.opened is not None:
        gl = etree.parse(os.path.join(doc_path, collection.opened))
        for entity in gl.xpath('//entity'):
            osm_script = etree.Element("osm-script")
            union = etree.SubElement(osm_script, "union")
            new_entity = Entity(entity.get("id"), entity.get("wikipedia"))
            new_entity.color = "0,0,0"
            if entity.get('status') is not None:
                new_entity.saved = entity.get('status')
            for osm, otype in zip(entity.get('osm').split(' '), entity.get('type').split(' ')):
                new_entity.osm.append(OSM(osm, otype))
                new_id = etree.SubElement(union, "id-query")
                new_id.set("type", otype)
                new_id.set("ref", osm)
            for p in entity.xpath('./p'):
                paragraph = iterelem(p, union, None)
                paragraph.id = p.get('id')
                new_entity.paragraphs.append(paragraph)
            entities.append(new_entity)
            print1 = etree.SubElement(osm_script, "print")
            print1.set("mode", "body")
            recurse = etree.SubElement(osm_script, "recurse")
            recurse.set("type", "down")
            print2 = etree.SubElement(osm_script, "print")
            print2.set("mode", "skeleton")
            new_entity.script = etree.tostring(osm_script).decode('utf-8')

    return render(request, 'annotator/index.html', {'entities': entities, 'collection': collection})


def iterelemout(elem, paragraph, divs):
    if elem.text is not None:
        paragraph.text = elem.text
    for child in elem.getchildren():
        if child.get("class") != "removed":
            link_id = child.get('id').replace("_text", "")
            link = etree.SubElement(elem, "link")
            link.set("id", link_id)
            div_id = link_id + "_hrefs"
            div = divs.xpath('./div[@id="' + div_id + '"]')
            if len(div) > 0:
                div = div[0]
                wikipedia_links = []
                for wikipedia in div.xpath('./a[@class="wikipedia"]'):
                    href = wikipedia.get("href").split("/")[-1]
                    wikipedia_links.append(href)
                link.set("wikipedia", " ".join(wikipedia_links))
                osm_links = []
                osm_types = []
                for osm in div.xpath('./a[@class="osm" and @href!=""]'):
                    href = osm.get("href").split("/")[-1]
                    htype = osm.get("href").split("/")[-2]
                    osm_links.append(href)
                    osm_types.append(htype)
                link.set("osm", " ".join(osm_links))
                link.set("type", " ".join(osm_types))
                paragraph.append(link)
                divs.remove(div)
            iterelemout(child, link, divs)
        else:
            append_text = child.text
            if child.tail is not None:
                append_text += child.tail
            if len(paragraph) == 0:
                paragraph.text += append_text
            else:
                paragraph[-1].tail += child.tail
    if elem.tail is not None:
        paragraph.tail = elem.tail


def get_statistics(gl):
    statistics = OrderedDict({"total": 0,
                              "annotated": 0,
                              "5": 0, "4": 0, "3": 0, "2": 0, "1": 0})
    for entity in gl.xpath('//entity'):
        statistics["total"] += 1
        if "status" in entity.attrib:
            statistics["annotated"] += 1
            status = entity.get("status")
            statistics[status] += 1 # What if status doesn't exist
    return statistics


@csrf_exempt
def save(request):
    file_name = None
    statistics = None
    if request.method == 'POST':
        form = forms.Form(request.POST)
        submission = html.fromstring(form.data["submission"])
        file_name = form.data["file_name"]
        file_path = "./documents/%s" % file_name
        gl = etree.parse(file_path)
        for modified in submission.xpath("//entity"):
            entity_name = modified.get("name")
            entity = gl.xpath('//entity[@id="' + entity_name + '"]')[0]
            entity_status = modified.get("value")
            entity.set("status", entity_status)
            for child in entity.getchildren():
                entity.remove(child)
            entity_divs = modified.xpath('./links/div')[0]
            for p in modified.xpath('./text/p'):
                paragraph = etree.SubElement(entity, "p")
                paragraph.set("id", p.get("id"))
                paragraph.set("num_links", str(len(entity_divs.xpath('./div'))))
                iterelemout(p, paragraph, entity_divs)
        gl.write(file_path, encoding="UTF-8", xml_declaration=True, pretty_print=True)
        statistics = get_statistics(gl)
    return render(request, 'annotator/save.html', {'file_name': file_name, 'statistics': statistics})
