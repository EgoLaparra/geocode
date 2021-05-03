package org.clulab.geonorm.formal

import org.locationtech.jts.geom.Geometry


case class CardinalPoint(point: String, expandDirection: Int, longitudinal: Boolean)

object CardinalPoint {

  def newCardinalPoint(value: String): CardinalPoint = value match {
    case "N" => CardinalPoint("N", 1, false)
    case "E" => CardinalPoint("E", 1, true)
    case "S" => CardinalPoint("S", -1, false)
    case "W" => CardinalPoint("W", -1, true)
    case _ => throw new UnsupportedOperationException
  }
}

class CardinalRegion(azimuth: Double, cardinalValues: Array[String]) {

  val cardinalPoints: Array[CardinalPoint] = cardinalValues.map(CardinalPoint.newCardinalPoint)
  val (expandX, expandY) = cardinalPoints.length match{
    case 1 => (1, 0)
    case 2 => (1, 1)
    case 4 => (0, 0)
    case _ => throw new UnsupportedOperationException
  }

  def cardinalSubRegion(region: Geometry, cardinalPoint: CardinalPoint): Geometry = {
    val bounds = region.getEnvelope.getCoordinates
    // boundsPoints (w, e, s, n)
    val boundsPoints = if (bounds.size == 5) {
      (bounds(0).x, bounds(2).x, bounds(0).y, bounds(2).y)
    } else {
      (bounds(0).x, bounds(0).x, bounds(0).y, bounds(0).y)
    }
    val expandValue = math.max(math.abs(bounds(0).x - bounds(2).x), math.abs(bounds(0).y - bounds(2).y))
    val expandDirectionX = this.expandX * cardinalPoint.expandDirection
    val expandDirectionY = this.expandY * cardinalPoint.expandDirection

    region
  }
}

object CardinalRegion {

  def newCardinalRegion(value: String): CardinalRegion = value match {
    case "N" => new CardinalRegion(0, Array("N"))
    case "NE" => new CardinalRegion(45, Array("N", "E"))
    case "E" => new CardinalRegion(90, Array("E"))
    case "SE" => new CardinalRegion(135, Array("S", "E"))
    case "S" => new CardinalRegion(180, Array("S"))
    case "SW" => new CardinalRegion(225, Array("S", "W"))
    case "W" => new CardinalRegion(270, Array("W"))
    case "NW" => new CardinalRegion(315, Array("N", "W"))
    case "C" => new CardinalRegion(0, Array("N", "E", "S", "W"))
    case _ => throw new UnsupportedOperationException
  }
}
