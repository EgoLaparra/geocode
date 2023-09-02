package org.clulab.geonorm.apps

import org.clulab.geonorm.scfg.GeoLocationExpressionParser
import org.clulab.geonorm.tools.Data

import java.io._
import scala.concurrent.ExecutionContext.Implicits.global
import scala.concurrent._
import scala.concurrent.duration._
import scala.util.Try


object XMLFileParserOperators {
  /**
    * Parses a GeoCoDe-data XML file.
    *
    */
  def main(args: Array[String]): Unit = {

    val parser = args match {
      case Array(xmlFile, outFile) =>
        val pw = new PrintWriter(new File(outFile ))
        val parser = new GeoLocationExpressionParser(subOptimal = false)
        val data = Data.fromPath(xmlFile)

        while (data.entities.hasNext) {
          val entity = data.nextEntity()
          val entity_id = entity.id.get
          println(s"Parsing entity $entity_id ...")
          pw.write(entity_id + "\n")
          val future = Future.apply {
            entity.expressions.map(parser.parse)
          }
          val locations = Try {
            Await.result(future, Duration("10 minute"))
          }.getOrElse(IndexedSeq.empty)

          val successParses = locations.filter(_.isSuccess).map(_.get)
          val expressionsWithShapes = entity.expressions.count(_.text.contains("SHP"))
          pw.write(s"\t${successParses.length} success from $expressionsWithShapes with shapes\n")
          if (successParses.nonEmpty) {
            successParses.seq.foreach(loc => pw.write("\t" + loc.toString  + "\n"))
          } else {
            pw.write("\tNo successful parse for this entity:\n")
            entity.expressions.foreach(e => pw.write("\t" + e.text  + "\n"))
          }
          pw.write("\n")
        }
        pw.close()
      case _ =>
        System.err.printf("usage: %s [xml-file] [output-table-name]", this.getClass.getSimpleName)
        System.exit(1)
        throw new IllegalArgumentException
    }
  }
}

