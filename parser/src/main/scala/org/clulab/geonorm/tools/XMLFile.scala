package org.clulab.geonorm.tools

import org.locationtech.jts.geom.Geometry

import scala.xml.{Node, XML}

object Data {
  def fromPath(xmlPath: String, database: Option[DataBase] = None, tsv: Option[TSV] = None) = apply(XML.loadFile(xmlPath), database, tsv)
  def apply(xml: Node, database: Option[DataBase] = None, tsv: Option[TSV] = None) = new Data(xml, database, tsv)
}
class Data(val xml: Node, database: Option[DataBase], tsv: Option[TSV]) {
  val entities: Iterator[Node] = tsv match {
    case None => (xml \\ "entity")
      .filter(_.attribute("status").map(_.text).contains("5")).toIterator
    case Some(t) => (xml \\ "entity")
      .filter(_.attribute("id").getOrElse(Seq()).exists(id => t.tsv.contains(id.text))).toIterator
  }
  def nextEntity(): Entity = Entity.apply(entities.next, database, tsv)
}


object Entity {

  val CONTINENTS = Array("Europe", "Africa", "Asia", "Oceania", "Americas", "South_America", "North_America")

  def apply(xml: Node, database: Option[DataBase], tsv: Option[TSV]): Entity = {
    val entity_id = xml.attribute("id").get.text
    val entity_name = xml.attribute("wikipedia").get.text.replaceAll("_", " ")
    val paragraph =
    for (child <- (xml \ "p").flatMap(p => p.child)) yield {
      if (child.isAtom) {
        (child.text, None, None)
      } else {
        val wikipedia = child.attribute("wikipedia").get.text
        if (CONTINENTS.contains(wikipedia) || wikipedia.contains("road_network"))
          (child.text, None, None)
        else {
          val toponym = child.text
          val shp_id = child.attribute("id").get.text.split("_").drop(2).mkString.toInt
          val shape_keys = child.attribute("osm").get.text.split(" ") zip child.attribute("type").get.text.split(" ")
          (s"SHP$shp_id", Some(toponym -> shp_id), Some(shp_id -> shape_keys))
        }
      }
    }
    val (textIndexSeq, toponymIndexSeq, shapeIndexSeq) = paragraph.unzip3
    val text: String = replace_target(clean_text(textIndexSeq.mkString), entity_name)
    println(text)
    val toponymMap: Map[String, Int] = toponymIndexSeq.flatten.toMap
    val shapeMap: Option[Map[Int, Array[Geometry]]] = database match {
      case Some(db) => Some(shapeIndexSeq.flatten.map{location => location._1 -> db.query(location._2)}.toMap)
      case _ => None
    }
    // This line replaces all the toponym ocurrences with their corresponding SHPid
    val expressions = tsv match {
      case None =>
        val processedText = toponymMap.keys.foldLeft(text)((newtext, toponym) =>
          newtext.replaceAll(s"(?<=\\W)${toponym}(?=\\W)", s"SHP${toponymMap(toponym)}"))
        val sentenceBoundary = "(?<=\\.)\\s+(?=[A-Z])".r
        sentenceBoundary.split(processedText).map(Expression(_, shapeMap)).toIndexedSeq
      case Some(t) =>
        t.tsv.get(entity_id).map(Expression(_, shapeMap)).toIndexedSeq
    }

    new Entity(Some(entity_id), expressions)
  }

  def applyFromText(sourceText: String): Entity = {
    val sentenceBoundary = "(?<=\\.)\\s+(?=[A-Z])".r
    val text = clean_text(sourceText)
    val expressions = sentenceBoundary.split(text).map(Expression(_)).toIndexedSeq
    new Entity(None, expressions)
  }

  def replace_target(text: String, entity_name: String): String = text
    .replaceAll(".+(?= is (an?|the|one of)\\b)", "TARGET")
    .replaceAll(entity_name, "TARGET")

  def clean_text(text: String): String = text
    .replaceAll("\\[[0-9]+\\]", "") // remove wikipedia refs
    .replaceAll("\\([^\\(\\)]+\\)", "") // remove text in parenthesis
    .replaceAll("\\'s", " \\'s") // add space to tokenize possessives
    .replaceAll("(?<=[0-9])\\.[0-9]+", "") // remove decimals
    .replaceAll("[0-9]+(°|′|'|″|\")([^A-Za-z]|N|W|S|E|)*(?=\\.)", "") // remove coordinates end of sentence
    .replaceAll("[0-9]+(°|′|'|″|\")([^A-Za-z]|N|W|S|E|)*", "") // remove coordinates

}
case class Entity(id: Option[String], expressions: IndexedSeq[Expression])


object Expression {
  def applyFromText(sourceText: String): Expression = new Expression(sourceText)
}
case class Expression(text: String, shapeMap: Option[Map[Int, Array[Geometry]]] = None)