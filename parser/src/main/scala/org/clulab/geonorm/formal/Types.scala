package org.clulab.geonorm.formal


import org.clulab.geonorm.tools.GeoTools._
import org.locationtech.jts.geom._


trait LocExpression {
  def isDefined: Boolean
}


/**
  * A location defined by a polygon formed by the coordinates of its boundary shape.
  */

trait Location extends LocExpression {
  def shape: Geometry

  def map {show_map(Array(shape))}

  def contains(location: Location): Boolean = shape.contains(location.shape)

  def locations(): Array[Location]
}

object Location {
  def unapply(location: Location): Option[Geometry] = Some(location.shape)

  def traverseLocations(loc: Location): Array[Location] =
    loc.locations().flatMap{l =>
      val nl = traverseLocations(l)
      nl :+ l
    }

  sealed trait Polygon extends (Location => Geometry)

  case object Shape extends Polygon {
    override def apply(location: Location): Geometry = location.shape
  }

}

case object UnknownLocation extends Location {
  val isDefined = false
  def shape: Geometry = throw new UnsupportedOperationException
  def locations() = throw new UnsupportedOperationException
}


/**
  * A GeoLocation is geo-political entity that can be found in database as GeoNames with
  * its corresponding geoid. Its boundary is stored in shape.
  */
case class GeoLocation(geoid: Int, geom: Option[Array[Geometry]] = None) extends Location {
  val isDefined = true
  lazy val shape: Geometry = processGeoLocation(geom.getOrElse(throw new UnsupportedOperationException))
  def locations(): Array[Location] = Array.empty
}


/**
  * A GeoCardinal is one of the directions in a compass.
  *
  */
case class GeoCardinal(value: String)  extends LocExpression{
  val isDefined = false
  val azimuth: Double = value match {
      case "N" => 0
      case "NE" => 45
      case "E" => 90
      case "SE" => 135
      case "S" => 180
      case "SW" => 225
      case "W" => 270
      case "NW" => 315
      case "C" => -1
      case _ => throw new UnsupportedOperationException
  }

  def shape(region: Geometry): Geometry = {
    if (azimuth < 0)
      distanceArc(region, diagonal(region) / 3)
    else {
      val cardinalArc = distanceArc(region, diagonal(region) * 2, Some(azimuth))
      val bufferedCardinalArc = buffer(cardinalArc, 0.05)
      between(region, bufferedCardinalArc)
    }
  }
}


case class SimpleLocation(location: Location, cardinal: Option[GeoCardinal] = None) extends Location {
  val isDefined = cardinal.isDefined
  lazy val shape: Geometry = cardinal match {
    case Some(point) => intersection(location.shape, point.shape(location.shape))
    case None => location.shape
  }
  def locations(): Array[Location] = Array(location)
}


case class SubLocation(location: Location) extends Location {
  val isDefined = location.isDefined
  lazy val shape: Geometry = location.shape
  def locations(): Array[Location] = Array(location)
}


case class Adjacent(location: Location, cardinal: Option[GeoCardinal] = None) extends Location {
  val isDefined = cardinal.isDefined
  lazy val shape: Geometry = cardinal match {
    case Some(point) => difference(point.shape(location.shape), location.shape)
    case None =>
      val bufferValue = buffer_by_factor(location.shape, factor = 5, force = true)
      difference(buffer(location.shape, bufferValue, force = true), location.shape)
  }
  def locations(): Array[Location] = Array(location)
}


case class Proximate(location: Location, cardinal: Option[GeoCardinal] = None) extends Location {
  val isDefined = cardinal.isDefined
  lazy val shape: Geometry = {
    val locationShp = difference(location.shape.buffer(0.1), location.shape)
    cardinal match {
      case Some(point) => intersection(locationShp, point.shape(locationShp))
      case None => locationShp
    }
  }
  def locations(): Array[Location] = Array(location)
}


case class Distance(location: Location, distance: Int, unit: String, cardinal: Option[GeoCardinal] = None) extends Location {
  val isDefined = cardinal.isDefined
  private val meters: Double = unit match {
    case "KM" => distance * 1000
    case "MI" => distance * 1609.344
    case "NMI" => distance * 1852.0
    case _ => throw new UnsupportedOperationException
  }
  lazy val shape: Geometry = {
    val arc = cardinal match {
      case Some(point) => distanceArc(location.shape, meters, Some(point.azimuth))
      case None => distanceArc(location.shape, meters)
      }
    val bufferValue = buffer_by_factor(location.shape, factor = 2, force = true)
    buffer(arc, bufferValue)
  }
  def locations(): Array[Location] = Array(location)
}


case class Union(locationSet: Set[Location]) extends Location {
  val isDefined = true
  lazy val shape: Geometry = collection(locationSet.map(_.shape).toArray)
  def locations(): Array[Location] = locationSet.toArray
}


case class Intersection(location1: Location, location2: Location) extends Location {
  val isDefined = true
  lazy val shape: Geometry = intersection(location1.shape, location2.shape)
  def locations(): Array[Location] = Array(location1, location2)
}


case class Between(from: Location, to: Location) extends Location {
  val isDefined = true
  lazy val shape: Geometry = {
    val between_polygon = between(from.shape, to.shape)
    difference(difference(between_polygon, from.shape), to.shape)
  }
  def locations(): Array[Location] = Array(from, to)
}


case class Route(from: Location, to: Location) extends Location {
  val isDefined = true
  lazy val shape: Geometry = {
    val fromPoint = from.shape.getCentroid
    val route = to match {
      case to: Route => makeLineString(fromPoint.getCoordinate +: to.shape.getCoordinates)
      case to: Location => {
        val toPoint = to.shape.getCentroid
        makeLineString(Array(fromPoint.getCoordinate, toPoint.getCoordinate))
      }
    }
    buffer(route, 0.001)
  }
  def locations(): Array[Location] = Array(from, to)
}
