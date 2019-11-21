import sys
from lxml import etree
import geopandas as gpd
from matplotlib import pyplot as plt
import contextily as ctx

import geometries as geo


gdf = gpd.GeoDataFrame()


def plot_geometries(geometry_list, color_list, lims=None):
    _, ax = plt.subplots(figsize=(100., 100.))
    for geometry, color in zip(geometry_list, color_list):
        if color is None:
            geometry.plot(ax=ax, alpha=0.)
        else:
            geometry_type = geo.get_geometry_type(geometry)
            if geometry_type == "ST_GeometryCollection":
                geometries = geo.dump_geometry(geometry)
            else:
                geometries = [geometry]
            for geom in geometries:
                pg = geo.make_geodataframe(geom, gdf)
                geom_type = geo.get_geometry_type(geom)
                if geom_type == "ST_Polygon":
                    pg.plot(ax=ax, alpha=0.5, color=color, linewidth=1.5, edgecolor=color)
                else:
                    pg.plot(ax=ax, alpha=1., color=color, linewidth=2.)
    ctx.add_basemap(ax, url=ctx.providers.OpenStreetMap.Mapnik, zoom=13, attribution_size=5)
    ax.axis('off')
    if lims is not None:
        ax.set_xlim(lims.minx[0], lims.maxx[0])
        ax.set_ylim(lims.miny[0], lims.maxy[0])
    plt.show()


def get_entity_geometries(entity):
    entity_geometries = []
    entity_osms = entity.get("osm").split(" ")
    entity_types = entity.get("type").split(" ")
    entity_wikipedia = entity.get("wikipedia")
    for osm, otype in zip(entity_osms, entity_types):
        if otype != "node":
            print(osm, otype, entity_wikipedia)
            osm_geometries = geo.get_geometries(osm, otype)
            for osm_geometry in osm_geometries:
                geometry = geo.process_geometry(osm_geometry)
                entity_geometries.append(geometry)
    return entity_geometries


if __name__ == "__main__":
    gl = etree.parse(sys.argv[1])
    exclude = []
    if len(sys.argv) == 4:
        exclude = sys.argv[3].split(",")
        print(exclude)
    entity = gl.xpath("//entity[@id='%s' and @status='5']" % sys.argv[2])[0]
    print(len(entity))
    if len(entity) == 1:
        entity_geometries = get_entity_geometries(entity)
        link_geometries = []
        for link in entity.xpath(".//link"):
            if link.get("id") not in exclude:
                link_geometries.extend(get_entity_geometries(link))

        geometries_for_plot = entity_geometries + link_geometries
        colors_for_plot = ["darkred"]*len(entity_geometries) + ["steelblue"]*len(link_geometries)

        envelope = geo.get_envelope(geo.unite_geometries(geometries_for_plot))
        envelope = geo.from_text("POLYGON((%s, %s, %s, %s, %s))"
                                 % tuple(["%s %s" % (c[0],c[1]) for c in [geo.get_coordinates(e) for e in envelope]]))
        pg = geo.make_geodataframe(envelope, gdf)
        pt = pg.scale(1.05, 1.05)
        geometries_for_plot.append(pt)
        colors_for_plot.append(None)

        plot_geometries(geometries_for_plot, colors_for_plot)
