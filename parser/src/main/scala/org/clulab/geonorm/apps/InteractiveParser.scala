package org.clulab.geonorm.apps

import java.io.File

import org.clulab.geonorm.scfg.GeoLocationExpressionParser
import org.clulab.geonorm.tools.Entity

import scala.io.Source
import scala.util.{Failure, Success}

object InteractiveParser {
  /**
    * Runs a demo of GeoLocationExpressionParser that reads time expressions from standard input and
    * writes their normalized forms to standard output.
    *
    * Note: This is only provided for demonstrative purposes.
    */
  def main(args: Array[String]): Unit = {

    // create the parser, using a grammar file if specified
    val parser = args match {
      case Array() =>
        new GeoLocationExpressionParser
      case Array(grammarPath) =>
        new GeoLocationExpressionParser(new File(grammarPath).toURI.toURL)
      case _ =>
        System.err.printf("usage: %s [grammar-file]", this.getClass.getSimpleName)
        System.exit(1)
        throw new IllegalArgumentException
    }

    System.out.println("Type in a geolocation expression (or :quit to exit)")

    // repeatedly prompt for a time expression and then try to parse it
    System.out.print(">>> ")
    for (line <- Source.stdin.getLines.takeWhile(_ != ":quit")) {
      val entity = Entity.applyFromText(line)
      for (source <- entity.expressions) {
        parser.parse(source) match {
          case Failure(exception) =>
            System.out.printf("Error: %s\n", exception.getMessage)
          case Success(location) =>
            System.out.println(location)
        }
      }
      System.out.print(">>> ")
    }
  }
}

