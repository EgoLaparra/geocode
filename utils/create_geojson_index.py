import geopandas as gpd
import os
import json

data_folder = "../clean_data/geojson"

out = {}
for filename in os.listdir(data_folder):
    with open(os.path.join(data_folder, filename),"r") as f:
        data = json.load(f)
    geo_df = gpd.GeoDataFrame.from_features(data["features"]).set_geometry("geometry")
    for n, row in geo_df.iterrows():
        osm_id = row['osm_id']
        if not os.path.exists(f"../clean_data_database/{osm_id[:2]}"):
            os.mkdir(f"../clean_data_database/{osm_id[:2]}")
        gpd.GeoDataFrame({"geometry":[row['geometry']]}).to_file(f"../clean_data_database/{osm_id[:2]}/{'_'.join(osm_id.split())}",driver="GeoJSON")

with open("osm_id_to_file_name.json","w") as f:
    json.dump(out, f)