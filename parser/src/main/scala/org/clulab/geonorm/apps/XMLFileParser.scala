package org.clulab.geonorm.apps

import java.net.URL

import org.locationtech.jts.geom.Geometry
import org.clulab.geonorm.scfg.{GeoLocationExpressionParser, OperatorTokenizer}
import org.clulab.geonorm.tools.{Data, DataBase, GeoTools, TSV}

import scala.concurrent._
import ExecutionContext.Implicits.global
import scala.concurrent.duration._
import scala.util.{Success, Try}


object XMLFileParser {
  /**
    * Parses a GeoCoDe-data XML file.
    *
    */

  def parseEntities(parser: GeoLocationExpressionParser, data: Data, database:DataBase): Unit = {
    var parsed = 0
    var shaped = 0
    while (data.entities.hasNext) {
      val entity = data.nextEntity()
      val entity_id = entity.id.get
      if (!database.exists(entity_id)) {
        println(s"Parsing entity $entity_id ...")
        val future = Future.apply {
          entity.expressions.map(parser.parse)
        }
        val locations = Try {
          Await.result(future, Duration("10 minute"))
        }.getOrElse(IndexedSeq.empty)

        val successParses = locations.filter(_.isSuccess).map(_.get)
        val definedParses = successParses.count(_.isDefined)
        val expressionsWithShapes = entity.expressions.count(_.text.contains("SHP"))
        println(s"\t$definedParses defined of ${successParses.length} success from $expressionsWithShapes with shapes")
        if (successParses.exists(_.isDefined) || successParses.length > 1) {
          parsed += 1
          val shapes: Array[Geometry] = successParses.flatMap { loc =>
            val shp = Try(loc.shape)
            shp match {
              case Success(s) if !s.isEmpty =>
                shaped += 1
                println("\tEntity parse successfully")
                println(loc) /// TODO: Remove this line!!!!
                Some(s)
              case _ =>
                println(s"\tShape calculation failed for: $loc")
                None
            }
          }.toArray
          if (shapes.length == 1) {
            database.insert(entity_id, shapes.head)
          }
          else if (shapes.length > 1) {
            val shpIntersection = GeoTools.intersection(shapes)
            if (shpIntersection.isEmpty)
              database.insert(entity_id, GeoTools.collection(shapes))
            else
              database.insert(entity_id, shpIntersection)
          }
        } else {
          println("\tNo successful parse for this entity:")
          entity.expressions.foreach(e => println(e.text))
        }
        println("")
      }
    }
    database.close()
    println(s"$parsed parsed, $shaped shaped")
  }
  def main(args: Array[String]): Unit = {

    val parser = args match {
      case Array(xmlFile, tableName) =>
        val parser = new GeoLocationExpressionParser(subOptimal = false)
        val database = new DataBase(tableName)
        val data = Data.fromPath(xmlFile, Some(database))
        parseEntities(parser, data, database)
      case Array(xmlFile, tableName, tsvFile) =>
        val grammar: URL = getClass.getResource("/org/clulab/geonorm/operators.grammar")
        val parser = new GeoLocationExpressionParser(subOptimal = false,
          grammarURL = grammar, tokenize = OperatorTokenizer)
        val database = new DataBase(tableName)
        val tsv = TSV.fromPath(tsvFile)
        val data = Data.fromPath(xmlFile, Some(database), Some(tsv))
        parseEntities(parser, data, database)
      case _ =>
        System.err.printf("usage: %s [xml-file] [output-table-name]", this.getClass.getSimpleName)
        System.exit(1)
        throw new IllegalArgumentException
    }
  }
}

