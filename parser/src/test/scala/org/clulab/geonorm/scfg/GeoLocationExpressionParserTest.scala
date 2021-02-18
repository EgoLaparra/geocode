package org.clulab.geonorm.scfg

import org.clulab.geonorm.formal._
import org.clulab.geonorm.tools.Expression
import org.junit.runner.RunWith
import org.scalatest.FunSuite
import org.scalatestplus.junit.JUnitRunner

import scala.util.Success

@RunWith(classOf[JUnitRunner])
class GeoLocationExpressionParserTest extends FunSuite{
  // create a new parser (using the default English grammar)
  val parser = new GeoLocationExpressionParser

  test("in") {
    assert(parser.parse(Expression.applyFromText("in SHP1"))
      === Success(SubLocation(SimpleLocation(GeoLocation(1)))))
    assert(parser.parse(Expression.applyFromText("a city in SHP1"))
      === Success(SubLocation(SimpleLocation(GeoLocation(1)))))
    assert(parser.parse(Expression.applyFromText("in the city of SHP1"))
      === Success(SubLocation(SimpleLocation(GeoLocation(1)))))
    assert(parser.parse(Expression.applyFromText("in the state of SHP1"))
      === Success(SubLocation(SimpleLocation(GeoLocation(1)))))
  }

  test("belongs") {
    assert(parser.parse(Expression.applyFromText("belongs to SHP1"))
      === Success(SubLocation(SimpleLocation(GeoLocation(1)))))
    assert(parser.parse(Expression.applyFromText("from SHP1"))
      === Success(SubLocation(SimpleLocation(GeoLocation(1)))))
    assert(parser.parse(Expression.applyFromText("from the city of SHP1"))
      === Success(SubLocation(SimpleLocation(GeoLocation(1)))))
  }

  test("subregion") {
    assert(parser.parse(Expression.applyFromText("in the east of SHP1"))
      === Success(SubLocation(SimpleLocation(GeoLocation(1), Some(GeoCardinal("E"))))))
    assert(parser.parse(Expression.applyFromText("in eastern SHP1"))
      === Success(SubLocation(SimpleLocation(GeoLocation(1), Some(GeoCardinal("E"))))))
    assert(parser.parse(Expression.applyFromText("in the eastern part of SHP1"))
      === Success(SubLocation(SimpleLocation(GeoLocation(1), Some(GeoCardinal("E"))))))
    assert(parser.parse(Expression.applyFromText("in the center of SHP1"))
      === Success(SubLocation(SimpleLocation(GeoLocation(1), Some(GeoCardinal("C"))))))
    assert(parser.parse(Expression.applyFromText("in central SHP1"))
      === Success(SubLocation(SimpleLocation(GeoLocation(1), Some(GeoCardinal("C"))))))
    assert(parser.parse(Expression.applyFromText("in the central part of SHP1"))
      === Success(SubLocation(SimpleLocation(GeoLocation(1), Some(GeoCardinal("C"))))))
  }

  test("between") {
    assert(parser.parse(Expression.applyFromText("between SHP1 and SHP2"))
      === Success(Between(SimpleLocation(GeoLocation(1)), SimpleLocation(GeoLocation(2)))))
    assert(parser.parse(Expression.applyFromText("from SHP1 to SHP2"))
      === Success(Between(SimpleLocation(GeoLocation(1)), SimpleLocation(GeoLocation(2)))))
  }

  test("proximate") {
    assert(parser.parse(Expression.applyFromText("close to the SHP1"))
      === Success(Proximate(SimpleLocation(GeoLocation(1)))))
    assert(parser.parse(Expression.applyFromText("close to SHP1"))
      === Success(Proximate(SimpleLocation(GeoLocation(1)))))
  }

  test("adjacent") {
    assert(parser.parse(Expression.applyFromText("borders with SHP1"))
      === Success(Adjacent(SimpleLocation(GeoLocation(1)))))
    assert(parser.parse(Expression.applyFromText("bordered by SHP1"))
      === Success(Adjacent(SimpleLocation(GeoLocation(1)))))
  }

  test("cardinal-adjacent") {
    assert(parser.parse(Expression.applyFromText("borders SHP1 to the north"))
      === Success(Adjacent(SimpleLocation(GeoLocation(1)), Some(GeoCardinal("S")))))
    assert(parser.parse(Expression.applyFromText("to the south of SHP1"))
      === Success(Adjacent(SimpleLocation(GeoLocation(1)), Some(GeoCardinal("S")))))
  }

  test("cardinal-distance") {
    assert(parser.parse(Expression.applyFromText("100 km east of SHP1"))
      === Success(Distance(SimpleLocation(GeoLocation(1)), 100, "KM", Some(GeoCardinal("E")))))
    assert(parser.parse(Expression.applyFromText("100 miles east of SHP1"))
      === Success(Distance(SimpleLocation(GeoLocation(1)), 100, "MI", Some(GeoCardinal("E")))))
  }

  test("intersection") {
    assert(parser.parse(Expression.applyFromText("in SHP1, SHP2"))
      === Success(SubLocation(SimpleLocation(SimpleLocation(GeoLocation(1))))))
    assert(parser.parse(Expression.applyFromText("in SHP1, SHP2, SHP3"))
      === Success(SubLocation(SimpleLocation(SimpleLocation(SimpleLocation(GeoLocation(1)))))))
  }
}
