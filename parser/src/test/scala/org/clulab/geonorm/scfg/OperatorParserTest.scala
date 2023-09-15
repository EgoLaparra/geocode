package org.clulab.geonorm.scfg

import java.net.URL

import org.clulab.geonorm.formal._
import org.clulab.geonorm.tools.Expression
import org.junit.runner.RunWith
import org.scalatest.FunSuite
import org.scalatestplus.junit.JUnitRunner

import scala.util.Success

@RunWith(classOf[JUnitRunner])
class OperatorParserTest extends FunSuite {
  // create a new parser (using the default English grammar)
  val grammar: URL = getClass.getResource("/org/clulab/geonorm/operators.grammar")
  val parser = new GeoLocationExpressionParser(grammarURL = grammar, tokenize = OperatorTokenizer)

  test("operators") {
    assert(parser.parse(
      Expression.applyFromText(
        "SubLocation(SimpleLocation(SimpleLocation(GeoLocation(1001,None),None),None))"))
      === Success(SubLocation(SimpleLocation(SimpleLocation(GeoLocation(1001,None),None),None))))
    assert(parser.parse(
      Expression.applyFromText(
        "SubLocation(SimpleLocation(GeoLocation(1001,None),Some(GeoCardinal(NE))))"))
      === Success(SubLocation(SimpleLocation(GeoLocation(1001,None),Some(GeoCardinal("NE"))))))
     assert(parser.parse(
      Expression.applyFromText(
        "Intersection(SubLocation(SimpleLocation(GeoLocation(1001,None),None)),Between(SimpleLocation(GeoLocation(1002,None),None),SimpleLocation(SimpleLocation(GeoLocation(1003,None),None),None)))"))
      === Success(Intersection(
      SubLocation(SimpleLocation(GeoLocation(1001,None),None)),Between(SimpleLocation(GeoLocation(1002,None),None),SimpleLocation(SimpleLocation(GeoLocation(1003,None),None),None)))))
    assert(parser.parse(
      Expression.applyFromText(
        "Intersection(SubLocation(SimpleLocation(SimpleLocation(GeoLocation(1001,None),None),None)),Adjacent(SimpleLocation(GeoLocation(1003,None),None),Some(GeoCardinal(N))))"))
      === Success(Intersection(
      SubLocation(SimpleLocation(GeoLocation(1001,None),None)),Between(SimpleLocation(GeoLocation(1002,None),None),SimpleLocation(SimpleLocation(GeoLocation(1003,None),None),None)))))

  }
}