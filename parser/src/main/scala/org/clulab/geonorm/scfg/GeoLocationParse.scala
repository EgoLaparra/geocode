package org.clulab.geonorm.scfg

import org.clulab.geonorm.formal._
import org.clulab.geonorm.scfg.SynchronousParser.Tree
import org.clulab.geonorm.tools.Expression

import scala.collection.immutable.Seq


trait TokenParser {
  def toInt(token: String): Int
  def toDimensionUnit(token: String): String
  def toReference(token: String): String
}

class DefaultTokenParser extends TokenParser {
    def toInt(token: String): Int = token.toInt
    def toDimensionUnit(token: String): String = token
    def toReference(token: String): String = token
}
object DefaultTokenParser extends DefaultTokenParser

private[geonorm] abstract class CanFail(name: String) {
  private[geonorm] def fail[T](tree: Tree): T = {
    throw new UnsupportedOperationException(
      "Don't know how to parse %s from %s".format(this.name, tree match {
        case tree: Tree.Terminal => tree.token
        case tree: Tree.NonTerminal => tree.rule.symbol + " -> " + tree.children.map {
          case child: Tree.Terminal => child.token
          case child: Tree.NonTerminal => child.rule.symbol
        }.mkString(" ")
      }))
  }
}

sealed abstract class GeoLocationParse

object GeoLocationParse extends CanFail("[GeoLocation]") with ((Tree, Expression) => GeoLocationParse) {

  def apply(tree: Tree, sourceExpression: Expression): GeoLocationParse = {
    this.applyNoImplicit(tree, sourceExpression, DefaultTokenParser)
  }

  private def applyNoImplicit(tree: Tree, sourceExpression: Expression, tokenParser: TokenParser): GeoLocationParse = {
    implicit val parser = tokenParser
    implicit val source = sourceExpression
    tree match {
      case tree: Tree.NonTerminal => tree.rule.basicSymbol match {
        case "[Location]" => LocationParse(tree)
        case _ => fail(tree)
      }
      case _ => fail(tree)
    }
  }
}

case class IntParse(value: Int)
object IntParse extends CanFail("[Int]") {
  def apply(tree: Tree)(implicit tokenParser: TokenParser): IntParse = tree match {
    case Tree.Terminal(number) =>
      IntParse(tokenParser.toInt(number))
    case tree =>
      val number = this.toDigits(tree).reverse.zipWithIndex.foldLeft(0){
        case (sum, (digit, index)) => sum + digit * math.pow(10, index).toInt
      }
      IntParse(number)
  }

  private def toDigits(tree: Tree): List[Int] = tree match {
    case Tree.Terminal(number) =>
      number.toInt :: Nil
    case Tree.NonTerminal(rule, children) if rule.basicSymbol == "[Int]" =>
      children.flatMap(this.toDigits)
    case _ => fail(tree)
  }
}

case class UnitParse(value: String)
object UnitParse extends CanFail("[Unit]") {
  def apply(tree: Tree)(implicit tokenParser: TokenParser): UnitParse = tree match {
    case Tree.Terminal(unit) =>
      UnitParse(tokenParser.toDimensionUnit(unit))
    case Tree.NonTerminal(rule, tree :: Nil) if rule.basicSymbol == "[Unit]" =>
      UnitParse(tree)
    case _ => fail(tree)
  }
}


case class CardinalParse(cardinal: String) {
  if (!Seq("N","S","E","W","NE","NW","SE","SW","C").contains(cardinal))
    throw new UnsupportedOperationException("cardinal %s is not valid".format(cardinal))
  def opposite(): String = {
    cardinal match {
      case "N" => "S"
      case "S" => "N"
      case "E" => "W"
      case "W" => "E"
      case "NE" => "SW"
      case "NW" => "SE"
      case "SE" => "NW"
      case "SW" => "NE"
      case _ => throw new UnsupportedOperationException("cardinal %s doesn't have opposite".format(cardinal))
    }
  }
}
object CardinalParse extends CanFail("[Cardinal]") {
  def apply(tree: Tree)(implicit tokenParser: TokenParser): CardinalParse = tree match {
    case tree: Tree.NonTerminal if tree.rule.basicSymbol == "[Cardinal]" => tree.children match {
      case Tree.Terminal(cardinal) :: Nil =>
        CardinalParse(tokenParser.toReference(cardinal))
    }
    case _ => fail(tree)
  }
}


sealed abstract class LocationParse extends GeoLocationParse {
  def toLocation: Location
}

object LocationParse extends CanFail("[Location]") {

  def apply(tree: Tree)(implicit tokenParser: TokenParser, source: Expression): LocationParse = tree match {
    case tree: Tree.NonTerminal if tree.rule.basicSymbol == "[Location]" => tree.children match {
      case (tree: Tree.NonTerminal) :: Nil  if tree.rule.basicSymbol == "[Location]" =>
        LocationParse(tree)
      case Tree.Terminal("Toponym") :: (tree: Tree.NonTerminal) :: Nil  if tree.rule.basicSymbol == "[Int]" =>
        ToponymParse(IntParse(tree).value)
      case Tree.Terminal("Simple") :: (tree: Tree.NonTerminal) :: Nil =>
        SimpleLocationParse(LocationParse(tree))
      case Tree.Terminal("Simple") :: (tree: Tree.NonTerminal) :: cardinal :: Nil =>
        SimpleLocationParse(LocationParse(tree), Some(CardinalParse(cardinal)))
      case Tree.Terminal("SubLocation") :: (tree: Tree.NonTerminal) :: Nil =>
        SubLocationParse(LocationParse(tree))
      case Tree.Terminal("Adjacent") :: tree :: Nil =>
        AdjacentParse(LocationParse(tree))
      case Tree.Terminal("Adjacent") :: tree :: cardinal :: Nil =>
        AdjacentParse(LocationParse(tree), Some(CardinalParse(cardinal)))
      case Tree.Terminal("Adjacent") :: tree :: Tree.Terminal("Opposite") :: cardinal :: Nil =>
        AdjacentParse(LocationParse(tree), Some(CardinalParse(cardinal)), opposite = true)
      case Tree.Terminal("Proximate") :: tree :: Nil =>
        ProximateParse(LocationParse(tree))
      case Tree.Terminal("Distance") :: tree :: distance :: unit :: Nil =>
        DistanceParse(LocationParse(tree), IntParse(distance).value, UnitParse(unit).value)
      case Tree.Terminal("Distance") :: tree :: distance :: unit :: cardinal :: Nil =>
        DistanceParse(LocationParse(tree), IntParse(distance).value, UnitParse(unit).value, Some(CardinalParse(cardinal)))
      case Tree.Terminal("Between") :: fromTree :: toTree :: Nil =>
        BetweenParse(LocationParse(fromTree), LocationParse(toTree))
      case Tree.Terminal("Union") :: tree1 :: tree2 :: Nil =>
        UnionParse(LocationParse(tree1), LocationParse(tree2))
      case Tree.Terminal("Intersection") :: tree1 :: tree2 :: Nil =>
        IntersectionParse(LocationParse(tree1), LocationParse(tree2))
      case Tree.Terminal("Route") :: tree1 :: tree2 :: Nil =>
        RouteParse(LocationParse(tree1), LocationParse(tree2))
      case _ => fail(tree)
    }
    case _ => fail(tree)
  }

  case class ToponymParse(referenceID: Int)(implicit source: Expression) extends LocationParse {
    def toLocation = if (source.shapeMap.isDefined) {
      GeoLocation(referenceID, Some(source.shapeMap.get(referenceID)))
    } else GeoLocation(referenceID)
  }

  case class SimpleLocationParse(tree: LocationParse, cardinal: Option[CardinalParse] = None) extends LocationParse {
    def toLocation = cardinal match {
      case Some(c) => SimpleLocation(tree.toLocation, Some(GeoCardinal(c.cardinal)))
      case None => SimpleLocation(tree.toLocation)
    }
  }

  case class SubLocationParse(tree: LocationParse) extends LocationParse {
    def toLocation = SubLocation(tree.toLocation)
  }

  case class AdjacentParse(tree: LocationParse, cardinal: Option[CardinalParse] = None, opposite: Boolean = false) extends LocationParse {
    def toLocation = cardinal match {
      case Some(c) if opposite => Adjacent(tree.toLocation, Some(GeoCardinal(c.opposite())))
      case Some(c) if !opposite => Adjacent(tree.toLocation, Some(GeoCardinal(c.cardinal)))
      case None => Adjacent(tree.toLocation)
    }
  }

  case class ProximateParse(tree: LocationParse) extends LocationParse {
    def toLocation = Proximate(tree.toLocation)
  }

  case class DistanceParse(tree: LocationParse, distance: Int, unit: String, cardinal: Option[CardinalParse] = None) extends  LocationParse {
    def toLocation = cardinal match {
      case Some(c) => Distance(tree.toLocation, distance, unit, Some(GeoCardinal(c.cardinal)))
      case None => Distance(tree.toLocation, distance, unit)
    }
  }

  case class BetweenParse(fromTree: LocationParse, toTree: LocationParse) extends LocationParse {
    def toLocation = Between(fromTree.toLocation, toTree.toLocation)
  }

  case class UnionParse(tree1: LocationParse, tree2: LocationParse) extends LocationParse {
    def toLocation = Union(Set(tree1.toLocation, tree2.toLocation))
  }

  case class IntersectionParse(tree1: LocationParse, tree2: LocationParse) extends LocationParse {
    def toLocation = Intersection(tree1.toLocation, tree2.toLocation)
  }

  case class RouteParse(tree1: LocationParse, tree2: LocationParse) extends LocationParse {
    def toLocation = Route(tree1.toLocation, tree2.toLocation)
  }

}

