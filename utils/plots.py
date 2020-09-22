import sys
from lxml import etree
from matplotlib import pyplot as plt
import geopandas as gpd
import contextily as ctx
from shapely.geometry import Polygon

from geometries import Geometries


def plot_geometries(geom, gdf, geometry_list, color_list, bound=False, lims=None):
    _, ax = plt.subplots(figsize=(100., 100.))
    for geometry, color in zip(geometry_list, color_list):
        if color is None:
            geometry.plot(ax=ax, alpha=0.)
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
                    geodataframe.plot(ax=ax, alpha=0.5, color=color, linewidth=1.5, edgecolor=color)
                else:
                    geodataframe.plot(ax=ax, alpha=1., color=color, linewidth=2.)
            if bound and geodataframe is not None:
                bound_dataframe(geodataframe, ax)
    ctx.add_basemap(ax, url=ctx.providers.OpenStreetMap.Mapnik, zoom=12, attribution_size=5)
    ax.axis('off')
    if lims is not None:
        ax.set_xlim(lims.minx[0], lims.maxx[0])
        ax.set_ylim(lims.miny[0], lims.maxy[0])

    plt.show()


def bound_dataframe(geodataframe, ax):
    dy = geodataframe.bounds.maxy[0] - geodataframe.bounds.miny[0]
    dx = geodataframe.bounds.maxx[0] - geodataframe.bounds.minx[0]
    if dy > dx:
        minx = geodataframe.bounds.minx[0] - (dy - dx) / 2
        maxx = geodataframe.bounds.maxx[0] + (dy - dx) / 2
        miny = geodataframe.bounds.miny[0]
        maxy = geodataframe.bounds.maxy[0]
    else:
        minx = geodataframe.bounds.minx[0]
        maxx = geodataframe.bounds.maxx[0]
        miny = geodataframe.bounds.miny[0] - (dx - dy) / 2
        maxy = geodataframe.bounds.maxy[0] + (dx - dy) / 2
    pol = Polygon([(minx, miny), (minx, maxy),
                   (maxx, maxy), (maxx, miny),
                   (minx, miny)])
    crs = {'init': 'epsg:3857'}
    pol = gpd.GeoDataFrame(index=[0], crs=crs, geometry=[pol])
    pol.plot(ax=ax, alpha=0.)


def get_entity_geometries(geom, entity):
    entity_geometries = []
    entity_osms = entity.get("osm").split(" ")
    entity_types = entity.get("type").split(" ")
    entity_wikipedia = entity.get("wikipedia")
    for osm, otype in zip(entity_osms, entity_types):
        if otype != "node":
            print(osm, otype, entity_wikipedia)
            osm_geometries = geom.get_geometries(osm, otype)
            for osm_geometry in osm_geometries:
                geometry = geom.process_geometry(osm_geometry)
                entity_geometries.append(geometry)
    return [geom.unite_geometries(entity_geometries)]


if __name__ == "__main__":
    geom = Geometries()
    gdf = gpd.GeoDataFrame()
    data_source = etree.parse(sys.argv[1])
    entity_id = sys.argv[2]
    print("Plot entity %s" % entity_id)
    exclude = []
    if len(sys.argv) > 3:
        exclude = sys.argv[4].split(",")
        print("Exclude entity %s" % exclude)
    prediction_table = None
    if len(sys.argv) == 5:
        prediction_table = sys.argv[4]
        print("From prediction")
    entity = data_source.xpath("//entity[@id='%s' and @status='5']" % entity_id)[0]
    if entity is not None and prediction_table is not None:
        entity_geometries = get_entity_geometries(geom, entity)
        predicted_geometry = [geom.get_predicted_geometry(data_source, entity_id)]
        geometries_for_plot = entity_geometries + predicted_geometry
        colors_for_plot = ["darkred"]*len(entity_geometries) + ["steelblue"]
        plot_geometries(geom, gdf, geometries_for_plot, colors_for_plot, bound=True)
    elif entity is not None:
        entity_geometries = get_entity_geometries(geom, entity)
        link_geometries = []
        for link in entity.xpath(".//link"):
            if link.get("id") not in exclude:
                link_geometries.extend(get_entity_geometries(geom, link))
        geometries_for_plot = entity_geometries + link_geometries
        colors_for_plot = ["darkred"]*len(entity_geometries) + ["steelblue"]*len(link_geometries)
        plot_geometries(geom, gdf, geometries_for_plot, colors_for_plot)
