package org.clulab.geonorm.formal

import org.junit.runner.RunWith
import org.scalatest.FunSuite
import org.scalatestplus.junit.JUnitRunner
import org.locationtech.jts.geom._
import org.geotools.geometry.jts.JTSFactoryFinder
import org.locationtech.jts.io.WKTReader


@RunWith(classOf[JUnitRunner])
class TypesTest extends FunSuite {

  val geometryFactory: GeometryFactory = JTSFactoryFinder.getGeometryFactory()
  val reader: WKTReader = new WKTReader(geometryFactory)

  val geometry1: Geometry = reader.read("POLYGON((1.0 1.0, 1.1 1.0, 1.1 1.1, 1.0 1.1, 1.0 1.0))")
  val geoLocation1: GeoLocation = GeoLocation(1, Some(Array(geometry1)))

  val geometry2: Geometry = reader.read("POLYGON((1.2 1.0, 1.3 1.0, 1.3 1.1, 1.2 1.1, 1.2 1.0))")
  val geoLocation2: GeoLocation = GeoLocation(2, Some(Array(geometry2)))


  test("subregion") {
    val west = SimpleLocation(geoLocation1, Some(GeoCardinal("W"))).shape.union()
    val westTarget: Geometry = reader.read("POLYGON ((1.0 1.0, 1.05 1.0, 1.05 1.1, 1.0 1.1, 1.0 1.0))")
    val westIntersection = westTarget.intersection(west)
    assert(westIntersection.getArea / west.getArea > 0.99)
    assert(westIntersection.getArea / westTarget.getArea > 0.99)

    val east = SimpleLocation(geoLocation1, Some(GeoCardinal("E"))).shape.union()
    val eastTarget: Geometry = reader.read("POLYGON ((1.05 1.0, 1.1 1.0, 1.1 1.1, 1.05 1.1, 1.05 1.0))")
    val eastIntersection = eastTarget.intersection(east)
    assert(eastIntersection.getArea / east.getArea > 0.99)
    assert(eastIntersection.getArea / eastTarget.getArea > 0.99)

    val south = SimpleLocation(geoLocation1, Some(GeoCardinal("S"))).shape.union()
    val southTarget: Geometry = reader.read("POLYGON ((1.0 1.0, 1.1 1.0, 1.1 1.05, 1.0 1.05, 1.0 1.0))")
    val southIntersection = southTarget.intersection(south)
    assert(southIntersection.getArea / south.getArea > 0.99)
    assert(southIntersection.getArea / southTarget.getArea > 0.99)

    val north = SimpleLocation(geoLocation1, Some(GeoCardinal("N"))).shape.union()
    val northTarget: Geometry = reader.read("POLYGON ((1.0 1.05, 1.1 1.05, 1.1 1.1, 1.0 1.1, 1.0 1.05))")
    val northIntersection = northTarget.intersection(north)
    assert(northIntersection.getArea / north.getArea > 0.99)
    assert(northIntersection.getArea / northTarget.getArea > 0.99)

    val southwest = SimpleLocation(geoLocation1, Some(GeoCardinal("SW"))).shape.union()
    val southwestTarget: Geometry = reader.read("POLYGON ((1.0 1.0, 1.0 1.1, 1.1 1.0, 1.0 1.0))")
    val southwestIntersection = southwestTarget.intersection(southwest)
    assert(southwestIntersection.getArea / southwest.getArea > 0.99)
    assert(southwestIntersection.getArea / southwestTarget.getArea > 0.99)

    val northwest = SimpleLocation(geoLocation1, Some(GeoCardinal("NW"))).shape.union()
    val northwestTarget: Geometry = reader.read("POLYGON ((1.0 1.0, 1.1 1.1, 1.0 1.1, 1.0 1.0))")
    val northwestIntersection = northwestTarget.intersection(northwest)
    assert(northwestIntersection.getArea / northwest.getArea > 0.99)
    assert(northwestIntersection.getArea / northwestTarget.getArea > 0.99)

    val southeast = SimpleLocation(geoLocation1, Some(GeoCardinal("SE"))).shape.union()
    val southeastTarget: Geometry = reader.read("POLYGON ((1.0 1.0, 1.1 1.1, 1.1 1.0, 1.0 1.0))")
    val southeastIntersection = southeastTarget.intersection(southeast)
    assert(southeastIntersection.getArea / southeast.getArea > 0.99)
    assert(southeastIntersection.getArea / southeastTarget.getArea > 0.99)

    val northeast = SimpleLocation(geoLocation1, Some(GeoCardinal("NE"))).shape.union()
    val northeastTarget: Geometry = reader.read("POLYGON ((1.0 1.1, 1.1 1.1, 1.1 1.0, 1.0 1.1))")
    val northeastIntersection = northeastTarget.intersection(northeast)
    assert(northeastIntersection.getArea / northeast.getArea > 0.99)
    assert(northeastIntersection.getArea / northeastTarget.getArea > 0.99)
  }


  test("adjacent") {
    val west = Adjacent(geoLocation1, Some(GeoCardinal("W"))).shape.union()
    val westTarget: Geometry = reader.read("POLYGON ((1.05 1.0, 0.805 0.826, 0.805 1.274, 1.05 1.1, 1.0 1.1, 1.0 1.0, 1.05 1.0)))")
    val westTargetIntersection = westTarget.intersection(west)
    assert(westTargetIntersection.getArea / west.getArea > 0.99)
    assert(westTargetIntersection.getArea / westTarget.getArea > 0.99)

    val northeast = Adjacent(geoLocation1, Some(GeoCardinal("NE"))).shape.union()
    val northeastTarget: Geometry = reader.read("POLYGON ((1.0 1.1, 1.064 1.383, 1.381 1.07, 1.1 1.0, 1.1 1.1, 1.0 1.1))")
    val northeastTargetIntersection = northeastTarget.intersection(northeast)
    assert(northeastTargetIntersection.getArea / northeast.getArea > 0.99)
    assert(northeastTargetIntersection.getArea / northeastTarget.getArea > 0.8)

  }

  test("distance") {
    val distance = Distance(geoLocation1, 10, "KM", Some(GeoCardinal("N"))).shape.union()
    assert(geoLocation1.shape.getCentroid.isWithinDistance(distance, 1))
  }

  test("between") {
    val between = Between(geoLocation1, geoLocation2).shape.union()
    val betweenTarget: Geometry = reader.read("POLYGON ((1.1 1.1, 1.2 1.1, 1.2 1, 1.1 1, 1.1 1.1))")
    val betweenIntersection = betweenTarget.intersection(between)
    assert(betweenIntersection.getArea / between.getArea > 0.99)
    assert(betweenIntersection.getArea / betweenTarget.getArea > 0.99)
  }
}