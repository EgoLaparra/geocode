def normalize(coordinates, min_limit=(-180, -90), max_limit=(180, 90)):
       xmin, ymin = min_limit
       xmax, ymax = max_limit
       x = (2. * coordinates[0] - (xmax + xmin)) / (xmax - xmin)
       y = (2. * coordinates[1] - (ymax + ymin)) / (ymax - ymin)
       if -1 <= x <= 1 and -1 <= y <= 1:
              return (x, y) 
       else:
              raise Exception(u"Coordinates exceed limits!!")

       
def denormalize(norm_coordinates, min_limit=(-180, -90), max_limit=(180, 90)):
       xmin, ymin = min_limit
       xmax, ymax = max_limit
       x = (norm_coordinates[0] * (xmax - xmin) + (xmax + xmin)) / 2
       y = (norm_coordinates[1] * (ymax - ymin) + (ymax + ymin)) / 2
       if xmin <= x <= xmax and ymin <= y <= ymax:
              return (x, y) 
       else:
              raise Exception(u"Coordinates exceed limits!!")


def coord_to_index_relative(coordinates, num_tiles, min_limit=(-180, -90), max_limit=(180, 90)):
        step = 2 / num_tiles
        norm_coordinates = normalize(coordinates, min_limit, max_limit)
        longitude = float(norm_coordinates[0]) + 1 if float(coordinates[0]) != 1 else 1.99
        latitude = -(float(norm_coordinates[1]) - 1) if float(coordinates[1]) != -1 else 1.99
        xindex = int(longitude / step)
        yindex = int(latitude / step)
        index = xindex + yindex * num_tiles
        if 0 <= index <= num_tiles ** 2:
               return index
        else:
               raise Exception(u"Shock horror!!")
 

def index_to_coord_relative(index, num_tiles, min_limit=(-180, -90), max_limit=(180, 90)):
        step = 2 / num_tiles
        yindex = int(index / num_tiles)
        xindex = index - yindex * num_tiles
        x = -1 + xindex * step + step / 2
        y = 1 - yindex * step - step / 2
        return denormalize((x, y), min_limit, max_limit)


def coord_to_index(coordinates, polygon_size):
        """
        Convert coordinates into an array (world representation) index. Use that to modify map_vector polygon value.
        :param coordinates: (latitude, longitude) to convert to the map vector index
        :param polygon_size: integer size of the polygon? i.e. the resolution of the world
        :return: index pointing into map_vector array
        """
        latitude = float(coordinates[0]) - 90 if float(coordinates[0]) != -90 else -179.99  # The two edge cases must
        longitude = float(coordinates[1]) + 180 if float(coordinates[1]) != 180 else 359.99  # get handled differently!
        if longitude < 0:
                longitude = -longitude
        if latitude < 0:
                latitude = -latitude
        x = int(360 / polygon_size) * int(latitude / polygon_size)
        y = int(longitude / polygon_size)
        if 0 <= x + y <= int(360 / polygon_size) * int(180 / polygon_size):
               return x + y
        else:
               raise Exception(u"Shock horror!!")



def index_to_coord(index, polygon_size):
        """
        Convert index (output of the prediction model) back to coordinates.
        :param index: of the polygon/tile in map_vector array (given by model prediction)
        :param polygon_size: size of each polygon/tile i.e. resolution of the world
        :return: pair of (latitude, longitude)
        """
        x = int(index / (360 / polygon_size))
        y = index % int(360 / polygon_size)
        if x > int(90 / polygon_size):
                x = -int((x - (90 / polygon_size)) * polygon_size)
        else:
                x = int(((90 / polygon_size) - x) * polygon_size)
        if y < int(180 / polygon_size):
                y = -int(((180 / polygon_size) - y) * polygon_size)
        else:
                y = int((y - (180 / polygon_size)) * polygon_size)
        return x, y


def bounded_grid(geom, num_tiles, min_limit=(-180, -90), max_limit=(180, 90)):
       xstep = (max_limit[0] - min_limit[0]) / num_tiles
       ystep = (max_limit[1] - min_limit[1]) / num_tiles
       grid = []
       ypos = max_limit[1]
       while ypos > min_limit[1]:
              grid_row = []
              xpos = min_limit[0]
              while xpos < max_limit[0]:
                     coordinates =[
                            [[xpos, ypos], [xpos + xstep, ypos]],
                            [[xpos + xstep, ypos - ystep], [xpos, ypos - ystep]]
                     ]
                     polygon = geom.from_text(
                            "POLYGON((%s))" % ", ".join([" ".join(map(str, point))
                                                         for e1, row in enumerate(coordinates)
                                                         for e2, point in enumerate(row)] +
                                                        ["%s %s" % (coordinates[0][0][0], coordinates[0][0][1])])
                            )
                     grid_row.append(polygon)
                     xpos += xstep
              grid.append(grid_row)
              ypos -= ystep
       return grid


def geometry_to_bitmap(geom, grid, geometry):
       bitmap = []
       for grid_row in grid:
              bitmap_row = []
              for polygon in grid_row:
                     bitmap_row.append(
                            1. if geom.instersects(geometry, polygon) else 0.
                            )
              bitmap.append(bitmap_row)
       return bitmap


def bitmap_to_geometry(geom, grid, bitmap):
       polygons = []
       for grid_row, bitmap_row in zip(grid, bitmap):
              polygons.extend([
                     polygon for polygon, bit in zip(grid_row, bitmap_row) if bit > .5
                     ])
       return geom.unite_geometries(polygons)


def geometry_group_bounds(geom, geometries, squared=True):
       bounding_diagonal = geom.get_bounding_diagonal(
              geom.unite_geometries(geometries)
       )
       if squared:
              bounding_diagonal = geom.get_bounding_diagonal(
                     geom.get_bounding_circle(bounding_diagonal)
              )              
       lower_point, upper_point = geom.dump_points(bounding_diagonal)
       min_coordinates = geom.get_coordinates(lower_point)
       max_coordinates = geom.get_coordinates(upper_point)
       return min_coordinates, max_coordinates
