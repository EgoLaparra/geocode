from gpt_operator import clean_response

data_file = "../gpt-4-output/09_19_01_for_eval.tsv"

a=clean_response("SubLocation(Intersection(Distance(SimpleLocation(GeoLocation(1004)), 2, 'KM', GeoCardinal('NW')), Proximate(SimpleLocation(GeoLocation(1003)))), SimpleLocation(GeoLocation(1001)))")

new_data = []
with open(data_file, 'r') as f:
    for line in f.readlines():
        new_line = clean_response(line)
        new_data.append(new_line)

with open("tmp.tsv", 'w') as f:
    for line in new_data:
        f.write(line)