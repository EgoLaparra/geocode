package org.clulab.geonorm.tools


import scala.io.Source


object TSV {
  def fromPath(tsvPath: String): TSV = {
    val tsv: Map[String, String] =
      Source.fromFile(tsvPath).getLines.map(_.split("\t")).collect {
          case Array(entity_id: String, operators: String) => entity_id -> operators
        }.toMap
    apply(tsv)
  }

  def apply(tsv: Map[String, String]) = new TSV(tsv)
}

case class TSV(tsv: Map[String, String])