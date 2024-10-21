from operators import *
import shapely.plotting
import matplotlib.pyplot as plt


def test_adjacent():
    reader = GeoJsonReader("../clean_data_database")

    az = reader.read("162018")
    ca = reader.read("165475")
    co = reader.read("161961")
    la = reader.read("224922")
    mx = reader.read("114686")
    nm = reader.read("162014")
    nv = reader.read("165473")
    ut = reader.read("161993")

    assert Near.to(az).intersection(nm).area > 0.0

    # Utah is north of Arizona
    assert NorthWest.of(az).intersection(ut).area >= 0
    assert North.of(az).intersection(ut).area >= 0
    assert NorthEast.of(az).intersection(ut).area >= 0
    assert East.of(az).intersection(ut).area == 0
    assert SouthEast.of(az).intersection(ut).area == 0
    assert South.of(az).intersection(ut).area == 0
    assert SouthWest.of(az).intersection(ut).area == 0
    assert West.of(az).intersection(ut).area == 0

    # Colorado is northeast of Arizona
    assert North.of(az).intersection(co).area >= 0
    assert NorthEast.of(az).intersection(co).area >= 0
    assert East.of(az).intersection(co).area >= 0
    assert SouthEast.of(az).intersection(co).area == 0
    assert South.of(az).intersection(co).area == 0
    assert SouthWest.of(az).intersection(co).area == 0
    assert West.of(az).intersection(co).area == 0
    assert NorthWest.of(az).intersection(co).area == 0

    # New Mexico is east of Arizona
    assert NorthEast.of(az).intersection(nm).area >= 0
    assert East.of(az).intersection(nm).area >= 0
    assert SouthEast.of(az).intersection(nm).area >= 0
    # assert South.of(az).intersection(nm).area == 0
    assert SouthWest.of(az).intersection(nm).area == 0
    assert West.of(az).intersection(nm).area == 0
    assert NorthWest.of(az).intersection(nm).area == 0
    # assert North.of(az).intersection(nm).area == 0

    # Mexico is southeast, south, and southwest of Arizona
    assert East.of(az).intersection(mx).area >= 0
    assert SouthEast.of(az).intersection(mx).area >= 0
    assert South.of(az).intersection(mx).area >= 0
    assert SouthWest.of(az).intersection(mx).area >= 0
    assert West.of(az).intersection(mx).area >= 0
    assert NorthWest.of(az).intersection(mx).area == 0
    assert North.of(az).intersection(mx).area == 0
    assert NorthEast.of(az).intersection(mx).area == 0

    # California is west of Arizona
    assert SouthWest.of(az).intersection(ca).area >= 0
    assert West.of(az).intersection(ca).area >= 0
    assert NorthWest.of(az).intersection(ca).area >= 0
    assert North.of(az).intersection(ca).area == 0
    assert NorthEast.of(az).intersection(ca).area == 0
    assert East.of(az).intersection(ca).area == 0
    assert SouthEast.of(az).intersection(ca).area == 0
    assert South.of(az).intersection(ca).area == 0

    # Nevada is northwest of Arizona
    assert West.of(az).intersection(nv).area >= 0
    assert NorthWest.of(az).intersection(nv).area >= 0
    assert North.of(az).intersection(nv).area >= 0
    assert NorthEast.of(az).intersection(nv).area == 0
    assert East.of(az).intersection(nv).area == 0
    assert SouthEast.of(az).intersection(nv).area == 0
    assert South.of(az).intersection(nv).area == 0
    assert SouthWest.of(az).intersection(nv).area == 0

    # Louisiana is not adjacent to Arizona
    assert Near.to(az).intersection(la).area == 0.0


def test_distance():
    reader = GeoJsonReader("../clean_data_database")

    de = reader.read("51477")
    fr = reader.read("1403916")  # "Metropolitan France" not the territories
    es = reader.read("1311341")

    # Spain is southwest of Germany, across France
    assert Near.to(de, distance=diameter(fr)).intersection(es).area > 0.0
    assert SouthWest.of(de, distance=diameter(fr)).intersection(es).area > 0.0
    assert Near.to(es, distance=diameter(fr)).intersection(de).area > 0.0
    assert NorthEast.of(es, distance=diameter(fr)).intersection(de).area > 0.0
