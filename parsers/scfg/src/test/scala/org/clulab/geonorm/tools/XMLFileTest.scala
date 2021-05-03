package org.clulab.geonorm.tools

import org.junit.runner.RunWith
import org.scalatest.FunSuite
import org.scalatestplus.junit.JUnitRunner


@RunWith(classOf[JUnitRunner])
  class XMLFileTest extends FunSuite  {
  val xml =
      <data>
        <entities>
          <entity id="E1" wikipedia="W1" osm="O1" type="T1" status="5">
          <p id="E1_001" num_links="2">Description of entity includes <link id="E1_001_001" wikipedia="W2" osm="O2" type="T2">Link1</link> and <link id="E1_001_002" wikipedia="W3" osm="O3" type="T3">Link2</link>.</p>
          </entity>
        </entities>
      </data>

  test("read-xml") {
    val data = Data.apply(xml)
    val entity: Entity = data.nextEntity()
    assert(entity.id === Some("E1"))

    val expression = entity.expressions(0)
    val description = "Description of entity includes SHP1 and SHP2."
    assert(expression.text === description)
  }
}
