from lxml import etree
import contextily as ctx
import pandas as pd

data_source = etree.parse("../dev_samples.xml")


with open("../gpt-4-output/09_19_01_for_eval.tsv") as f:
    lines = f.readlines()

output = []
for line in lines:

    entity_id, operator = line.strip().split('\t')
    input_sentence_entity = data_source.xpath("//entity[@id='%s']/p/text()" % entity_id)
    input_sentence_link_id = [link.get("id") for link in data_source.xpath("//entity[@id='%s']/p/link" % entity_id)]
    input_sentence_links = data_source.xpath("//entity[@id='%s']/p/link/text()" % entity_id)

    input_sentence = ''
    for i in range(len(input_sentence_links)):
        input_sentence += input_sentence_entity[i]
        input_sentence += f" {input_sentence_link_id[i]} "
        input_sentence += input_sentence_links[i]
    input_sentence += input_sentence_entity[-1]
    input_sentence = input_sentence.replace('\n', ' ')
    output.append((entity_id, input_sentence.strip(), operator))

df = pd.DataFrame(output)
df.to_csv("operators_and_input.tsv", index=False, header=False,sep='\t')
