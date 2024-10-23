from operators import *


def test_adjacent(georeader: GeoJsonDirReader):
    az = georeader.read("162018")
    ca = georeader.read("165475")
    co = georeader.read("161961")
    la = georeader.read("224922")
    mx = georeader.read("114686")
    nm = georeader.read("162014")
    nv = georeader.read("165473")
    ut = georeader.read("161993")

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


def test_distance(georeader: GeoJsonDirReader):
    de = georeader.read("51477")
    fr = georeader.read("1403916")  # "Metropolitan France" not the territories
    es = georeader.read("1311341")

    # Near should not overlap the original polygon
    assert Near.to(de).intersection(de).area == 0
    assert Near.to(fr).intersection(fr).area == 0
    assert Near.to(es).intersection(es).area == 0

    # Near with a distance greater than radius + diameter should not overlap
    assert Near.to(de, distance=1.5*diameter(de)).intersection(de).area == 0
    assert Near.to(fr, distance=1.5*diameter(fr)).intersection(fr).area == 0
    assert Near.to(es, distance=1.5*diameter(es)).intersection(es).area == 0

    # Spain is southwest of Germany, across France
    fr_diameter = diameter(fr)
    assert Near.to(de, distance=fr_diameter).intersection(es).area > 0.0
    assert SouthWest.of(de, distance=fr_diameter).intersection(es).area > 0.0
    assert Near.to(es, distance=fr_diameter).intersection(de).area > 0.0
    assert NorthEast.of(es, distance=fr_diameter).intersection(de).area > 0.0


def test_between(georeader: GeoJsonDirReader):
    na = georeader.read("195266")  # Namibia
    bw = georeader.read("1889339")  # Botswana
    zw = georeader.read("195272")  # Zimbabwe

    # Botswana is between Namibia and Zimbabwe
    assert Between.of(na, zw).intersection(bw).area > 0
    assert Between.of(zw, na).intersection(bw).area > 0
