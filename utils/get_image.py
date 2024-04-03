import sys
import numpy as np
from lxml import etree
from PIL import Image
from geometries import Geometries
import preprocess as pp


geom = Geometries()

data = etree.parse(sys.argv[1])
entities = data.xpath("//entity")
entity = entities[int(sys.argv[3])]
entity_geoms = [geom.get_entity_geometry(entity)]
for l in entity.xpath(".//link"):
    try:
        entity_geoms.append(geom.get_entity_geometry(l))
    except Exception as e:
        print(e)

united_envelope = geom.get_envelope(
        geom.unite_geometries(entity_geoms)
)
union_points = geom.dump_points(
    united_envelope
)
union_coordinates = [geom.get_coordinates(point) for point in union_points]
xmax, ymax = np.max(union_coordinates, axis=0)
xmin, ymin = np.min(union_coordinates, axis=0)
point_min = geom.transform_geometry(
    geom.from_text("POINT(%s %s)" % (xmin, ymin))
)
point_max = geom.transform_geometry(
    geom.from_text("POINT(%s %s)" % (xmax, ymax))
)

grid_size = int(sys.argv[2])
grid = pp.bounded_grid(geom, grid_size, min_limit=(xmin, ymin), max_limit=(xmax, ymax))
colors = [[255, 255, 255],
          [255, 0, 0], [0, 255, 0], [0, 0, 255],
          [127, 127, 0], [0, 127, 127], [127, 0, 127]]

images = []
for g, c in zip(entity_geoms, colors):
    g = geom.get_boundary(g)
    images.append(pp.geometry_to_image(geom, grid, g, c))
images = np.array(images, dtype="f").reshape(len(images), -1, 3)
images[images == 0] = np.nan
mean_image = [tuple(i) for i in np.nan_to_num(np.nanmean(images, axis=0)).astype(int)]

image = Image.new("RGB", (grid_size, grid_size))
image.putdata(mean_image)

if len(sys.argv) == 5:
    image.save(sys.argv[4])
else:
    image.show()