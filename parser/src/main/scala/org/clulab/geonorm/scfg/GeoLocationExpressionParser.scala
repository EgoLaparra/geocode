package org.clulab.geonorm.scfg

import java.net.URL
import java.util.logging.Logger

import scala.collection.immutable.IndexedSeq
import scala.io.Source
import scala.util.{Failure, Success, Try}
import org.clulab.geonorm.formal._
import org.clulab.geonorm.tools.Expression


/**
  * A parser for natural language expressions of geolocations, based on a synchronous context free grammar.
  * Typical usage:
  * {{{
  * // create a new parser (using the default English grammar)
  * val parser = new GeoLocationParser
  * // parse an expression
  * val Success(location) = parser.parse("between SHP1 and SHP2")
  * // get the MultiPolygon from the Location
  * val value = location.shape
  * }}}
  *
  * @constructor Creates a parser from a URL to a grammar file.
  * @param grammarURL The URL of a grammar file, in [[SynchronousGrammar.fromString]] format. If not
  *        specified, the default English grammar on the classpath is used. Note that if another
  *        grammar is specified, it may be necessary to override the [[tokenize]] method.
  * @param tokenize A function that splits a string into tokens. The default tokenizer is appropriate
  *        for the default English grammar. Other languages may require alternate tokenizers.
  */
class GeoLocationExpressionParser (grammarURL: URL = classOf[GeoLocationExpressionParser].getResource("/org/clulab/geonorm/en.grammar"),
                         tokenize: String => IndexedSeq[String] = DefaultTokenizer, subOptimal:Boolean = false) {
    private val logger = Logger.getLogger(this.getClass.getName)
    private val grammarText = Source.fromURL(grammarURL, "UTF-8").mkString
    private val grammar = SynchronousGrammar.fromString(grammarText)
    private val sourceSymbols = grammar.sourceSymbols()
    private val parser = new SynchronousParser(grammar, subOptimal)

  /**
    * Tries to parse a source string into a single [[Location]] object.
    *
    * @param sourceText The input string in the source language.
    * @return The most likely [[Location]] parse according to the parser's heuristic.
    */
  def parse(source: Expression): Try[Location] = {
    this.parseAll(source).map(_.head)
  }

  /**
    * Try to parse a source string into possible [[Location]] objects.
    *
    * @param sourceText The input string in the source language.
    * @return A sequence of [[Location]] objects representing the possible parses. The sequence is
    *         sorted by a heuristic that tries to put the most promising parses first.
    */
  def parseAll(source: Expression): Try[Seq[Location]] = {
    val tokens = this.tokenize(source.text).filter { token =>
      this.sourceSymbols.contains(token) || SynchronousGrammar.isNumber(token)
    }

    // parse the tokens into GeoLocationParses, failing if there is a syntactic error
    val parsesTry =
      try {
        val trees = this.parser.parseAll(tokens)
        // two unique trees can generate the same GeoLocationParse, so remove duplicates
        Success(trees.map(GeoLocationParse(_, source)).toSet)
      } catch {
        case e: UnsupportedOperationException => Failure(e)
      }

    // if there was no syntactic error, convert the GeoLocationParses to Locations
    parsesTry match {
      case Failure(e) => Failure(e)

      case Success(parses) =>
        // assume that the grammar ambiguity for any expression is at most 2
        if (parses.size > 2) {
          val message = "Expected no more than 2 parses for \"%s\", found:\n  %s"
          this.logger.warning(message.format(source.text, parses.mkString("\n  ")))
        }

        // try to convert each GeoLocationParse to a Location
        val locationTries = for (parse <- parses) yield {
          try {
            Success(parse match {
              case parse: LocationParse => parse.toLocation
            })
          } catch {
            case e @ (_: UnsupportedOperationException) => Failure(e)
          }
        }

        // if there all GeoLocationParses had semantic errors, fail
        val locations = locationTries.collect { case Success(location) => location }
        if (locations.isEmpty) {
          locationTries.collect { case Failure(e) => Failure(e) }.head
        }
        // otherwise, sort the Locations by the heuristic
        else {
          Success(locations.toSeq.sortBy(measureByHeuritic).reverse)
        }
    }
  }

  def measureByHeuritic(location: Location): Double = {
    Location.traverseLocations(location).foldRight(0.0) { (loc, count) =>
      loc match {
        case _: SubLocation => count + 0.9 // This prioritizes Single locations against Compositions
        case _ => count + 1
      }
    }
  }
}



object DefaultTokenizer extends (String => IndexedSeq[String]) {
  final val wordBoundary = "\\b".r
  final val letterNonLetterBoundary = "(?<=[^\\w])(?=[\\w])|(?<=[\\w])(?=[^\\w])".r

  def apply(sourceText: String): IndexedSeq[String] = {
    val tokens = for (untrimmedWord <- this.wordBoundary.split(sourceText).toIndexedSeq) yield {
      val word = untrimmedWord.trim
      if (word.isEmpty) {
        IndexedSeq.empty[String]
      }
      else if (word.matches("^SHP\\d+$")) {
        IndexedSeq(word.substring(0, 3), word.substring(3))
      }
      // otherwise, split at all letter/non-letter boundaries
      else {
        this.letterNonLetterBoundary.split(word).toIndexedSeq.map(_.trim.toLowerCase).filterNot(_.isEmpty)
      }
    }
    tokens.flatten
  }
}


object OperatorTokenizer extends (String => IndexedSeq[String]) {
  final val operatorSplitter = "((?<=(,|\\(|\\)))|(?=(,|\\(|\\))))".r

  def apply(sourceText: String): IndexedSeq[String] = {
    this.operatorSplitter.split(sourceText).toIndexedSeq
  }
}

