import json
input_file = "scores_1214.json"

with open(input_file) as f:
    data = json.load(f)

overall_recall = 0
overall_precision = 0
overall_f1 = 0

total_non_empty_shapes = 0
total_prediction = 0
total_gold = len(data)

for _, d in data.items():
    if d["score_type"] == 0:
        total_non_empty_shapes += 1
        total_prediction += 1
        overall_recall += d["score"]["gold"][0][0]
        overall_precision += d["score"]["gold"][0][1]
        overall_precision += d["score"]["gold"][0][2]
    elif d["score_type"] == 1:
        total_prediction += 1

print(overall_recall/total_non_empty_shapes, overall_precision/total_non_empty_shapes, overall_f1/total_non_empty_shapes)
print(overall_recall/total_prediction, overall_precision/total_prediction, overall_f1/total_prediction)
print(overall_recall/total_gold, overall_precision/total_gold, overall_f1/total_gold)