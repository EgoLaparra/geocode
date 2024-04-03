import argparse
import re
import geopandas as gpd
from operators import *
from matplotlib import pyplot as plt
import json

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input_data", type=str, default="../clean_data/dev_samples.xml")
    parser.add_argument("--operator_file", type=str, default="geocode_generation_clean.json")
    parser.add_argument("--output_file", type=str, default="codellama_operator_prediction_1213.geojson")

    args = parser.parse_args()
    return args

# ref_ids = ["1001","1002"]
# input_str = "GL586_341	GeoLocation(1001), GeoLocation(1002)"

ref_ids = ["57398"]
# input_str = "GL586_341	Intersection(GeoLocation(1001), Between(SubLocation(GeoLocation(1002), GeoCardinal('N')), GeoLocation(1003)))"
input_str_debug = "GL532_390	Adjacent(OSM304938, GeoCardinal(S))"




def preprocess_input_str(input_str, data_source):
    entity_id, operators_str = input_str.split('\t')
    output_str = operators_str

    # wrap reference ids with SimpleLocation and GeoLocation
    all_refs = re.findall(r'OSM[0-9_]+', operators_str)
    for ref in set(all_refs):
        output_str = output_str.replace(ref, f"GeoLocation('{ref[3:]}',entity_id='{entity_id}',data_source=data_source)")

    # wrap an extra Intersection
    output_str = f"Intersection({output_str})"

    return output_str

def preprocess_json_input_str(input_str,  entity_id):

    if input_str.startswith("```python"):
        input_str = input_str[9:-4]
    operators_str = input_str.strip()
    output_str = operators_str

    # wrap reference ids with GeoLocation
    all_refs = re.findall(r'OSM[0-9_]+', operators_str)
    for ref in set(all_refs):
        output_str = output_str.replace(ref, f"GeoLocation('{ref[3:]}',entity_id='{entity_id}',data_source=data_source)")

    # wrap an extra Intersection
    output_str = f"Intersection({output_str})"

    return output_str

# plot the shapes
from plots import bound_dataframe
def plot_geometries(geometry_list, color_list, alpha_list, entity_id, output_file_name=None, bound=False, lims=None):
    _, ax = plt.subplots(figsize=(100., 100.))
    geom = Geometries()
    gdf = gpd.GeoDataFrame()
    for geometry, color, alpha in zip(geometry_list, color_list, alpha_list):
        if color is None:
            geometry.plot(ax=ax, alpha=0.)
        else:
            if type(geometry) == gpd.GeoDataFrame:
                geometry.plot(ax=ax, alpha=alpha, color=color, linewidth=2.)
            else:
                geometry_type = geom.get_geometry_type(geometry)
                if geometry_type == "ST_GeometryCollection":
                    geometries = geom.dump_geometry(geometry)
                else:
                    geometries = [geometry]
                geodataframe = None
                for geometry in geometries:
                    geodataframe = geom.make_geodataframe(geometry, gdf)
                    geom_type = geom.get_geometry_type(geometry)
                    if geom_type == "ST_Polygon" or geom_type == "ST_MultiPolygon":
                        geodataframe.plot(ax=ax, alpha=alpha, color=color, linewidth=1.5, edgecolor=color)
                    else:
                        geodataframe.plot(ax=ax, alpha=1., color=color, linewidth=2.)
                if bound and geodataframe is not None:
                    bound_dataframe(geodataframe, ax)
    # ctx.add_basemap(ax, url=ctx.providers.OpenAIP, zoom=12, attribution_size=5)
    ax.axis('off')
    if lims is not None:
        ax.set_xlim(lims.minx[0], lims.maxx[0])
        ax.set_ylim(lims.miny[0], lims.maxy[0])

    if output_file_name is None:
        output_file_name = entity_id
    plt.savefig(f"{output_file_name}.png")

def main():
    args = parse_args()
    input_data = args.input_data
    operator_file = args.operator_file
    data_source = etree.parse(input_data)

    with open(operator_file) as f:
        data = json.load(f)

    total = len(data)
    success = 0
    output = {"entity_id":[],"geometry":[]}
    # input_strs = [input_str_debug]
    for key in data:
        print(f"Parsing: {key}")
        # input_str = input_str_debug
        input_str_preprocessed = preprocess_json_input_str(data[key][1], key)

        try:
            output_shape = eval(input_str_preprocessed)
            output["entity_id"].append(key)
            output["geometry"].append(output_shape.geoms.iloc[0]['geom'])
            success += 1
            print("Success!")
            print("--------------------------------------------------------------------")
            # ref_geoms = [GeoLocation(ref, entity_id=key, data_source=data_source).geoms for ref in ref_ids]
            # target_color = "darkred"
            # ref_color = "steelblue"
            # colors_for_plot = [target_color] + [ref_color]*len(ref_geoms)
            # alphas_for_plot = [0.5] * len(colors_for_plot)
            # plot_geometries([output_shape.geoms]+ref_geoms, colors_for_plot, alphas_for_plot, key,output_file_name=f"figures/{key}", bound=True)
        except Exception as e:
            print(f"Error message: {e}")
            print(f"Preprocessed string: {input_str_preprocessed}")
            print("Fail!")
            print("--------------------------------------------------------------------")
            continue



    print(success)
    output_df = gpd.GeoDataFrame(output, geometry="geometry")
    output_df = output_df.set_crs(epsg=4326)

    output_df.to_file(args.output_file, driver='GeoJSON')

if __name__ == "__main__":
    main()








    # colors_for_plot = [target_color]
    # alphas_for_plot = [0.5] * len(colors_for_plot)
    # plot_geometries([output_shape.geoms], colors_for_plot, alphas_for_plot, key, output_file_name=f"figures/{key}.png", bound=True)