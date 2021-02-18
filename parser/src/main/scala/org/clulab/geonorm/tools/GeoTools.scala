package org.clulab.geonorm.tools

import java.awt.{Color, Rectangle}
import java.awt.geom.AffineTransform
import java.awt.image.BufferedImage
import java.io.File

import javax.imageio.ImageIO
import org.geotools.map._
import org.geotools.data.DataUtilities
import org.geotools.feature.simple.SimpleFeatureBuilder
import org.geotools.geometry.jts.{JTS, JTSFactoryFinder}
import org.geotools.styling.SLD
import org.geotools.swing.JMapFrame
import org.geotools.referencing.operation.transform.AffineTransform2D
import org.geotools.referencing.GeodeticCalculator
import org.geotools.renderer.lite.StreamingRenderer
import org.locationtech.jts.geom._
import org.locationtech.jts.geom.impl.CoordinateArraySequenceFactory
import org.locationtech.jts.operation.linemerge.LineMerger

import scala.util.Try


object GeoTools {

  def generate_map(geometries: Array[Geometry], colorsOpt: Option[Array[String]] = None): MapContent = {
    val TYPE = DataUtilities.createType("geom", "geom:Geometry")
    val builder = new SimpleFeatureBuilder(TYPE)
    val map = new MapContent
    map.setTitle("GeoCoDe")

    val colorsToPlot = colorsOpt match {
      case Some(colors) => colors.map(Color.decode)
      case None => Array.fill(geometries.length)(Color.BLUE)
    }
    val geometriesToPlot: Array[(Geometry, Color)] = (geometries zip colorsToPlot).flatMap {
      case (g: GeometryCollection, c: Color) => for (dg <- dumpGeometry(g)) yield (dg, c)
      case (g, c: Color) => Array((g, c))
    }
    for ((geometry, color) <- geometriesToPlot) {
      val style = geometry match {
        case _: Point => SLD.createPointStyle("circle", color, color, 0.5f, 10.0f)
        case _: MultiPoint => SLD.createPointStyle("circle", color, color, 0.5f, 10.0f)
        case _: LineString => SLD.createLineStyle(color, 2.0f)
        case _: MultiLineString => SLD.createLineStyle(color, 2.0f)
        case _: Polygon if color.equals(Color.WHITE) => SLD.createPolygonStyle(Color.WHITE, color, 0.0f)
        case _: Polygon => SLD.createPolygonStyle(null, color, 0.5f)
        case _: MultiPolygon => SLD.createPolygonStyle(null, color, 0.5f)
      }
      builder.add(geometry)
      val location = builder.buildFeature(null)
      val layer = new FeatureLayer(DataUtilities.collection(Array(location)), style)
      map.addLayer(layer)
    }

    val envelope = collection(geometries).getEnvelope
    builder.add(envelope)
    val location = builder.buildFeature(null)
    val style = SLD.createLineStyle(Color.GRAY, 2.0f)
    val layer = new FeatureLayer(DataUtilities.collection(Array(location)), style)
    map.addLayer(layer)

    map
  }


  def show_map(geometries: Array[Geometry], colorsOpt: Option[Array[String]] = None) {
    val map = generate_map(geometries, colorsOpt)
    val mapFrame = new JMapFrame(map)
    mapFrame.enableToolBar(true)
    mapFrame.enableStatusBar(true)
    mapFrame.setSize(1000, 1000)
    mapFrame.setVisible(true)
  }


  def save_map(file: String, geometries: Array[Geometry], colorsOpt: Option[Array[String]] = None) {
    val map = generate_map(geometries, colorsOpt)
    val renderer = new StreamingRenderer()
    renderer.setMapContent(map)

    val mapBounds = map.getMaxBounds
    val heightToWidth = mapBounds.getSpan(1) / mapBounds.getSpan(0)
    val imageBounds = new Rectangle(
      0, 0, 500, Math.round(500 * heightToWidth).toInt
    )

    val image = new BufferedImage(imageBounds.width, imageBounds.height, BufferedImage.TYPE_INT_RGB)

    val graphics = image.createGraphics()
    graphics.setPaint(Color.WHITE)
    graphics.fill(imageBounds)

    renderer.paint(graphics, imageBounds, mapBounds)
    val fileToSave = new File(file)
    ImageIO.write(image, "png", fileToSave)
    map.dispose()
  }


  def dumpGeometry(geometry: Geometry) : Array[Geometry] = {
    for (i <- 0 until geometry.getNumGeometries) yield
      geometry.getGeometryN(i)
  }.toArray


  def processLineString(geometry: Geometry): Geometry = {
    geometry match {
      case lineString: LineString if lineString.isClosed => makePolygon(lineString)
      case lineString: LineString => lineString
      case _ => throw new Exception("Something went wrong merging LineString")
    }
  }


  def processGeometry(geometry: Geometry): Array[Geometry] = {
    geometry match {
      case geom: LineString => Array(processLineString(geom))
      case geom: MultiLineString =>
          dumpGeometry(mergeLines(geom)).map(processLineString)
      case geom: Point => Array(geom)
      case geom: MultiPoint => Array(geom)
      case geom: Polygon => Array(geom)
      case _ => throw new Exception("Geometry is not LineString, MultiLineString, Point or MultiPoint")
    }
  }

  def processGeoLocation(geometries: Array[Geometry]): Geometry = {
    val processedGeometries = geometries.flatMap(processGeometry)
    // TODO: Remove the Try
    val geometryUnion = Try(union(processedGeometries)).getOrElse(collection(processedGeometries))
    val geometryDump = dumpGeometry(geometryUnion).map(buffer(_, 0.02))
    Try(union(geometryDump)).getOrElse(collection(geometryDump))
  }

  def pickReferenceGeometry(geometry: Geometry): Geometry = {
    val geometries = dumpGeometry(geometry)
    val geometryNumPoints = geometries zip geometries.map(_.getNumPoints.toDouble)
    val totalNumPoints = geometryNumPoints.map(_._2).sum
    val geometriesWithoutOutliers = geometryNumPoints.filter(_._2 / totalNumPoints > 0.1).map(_._1)
    if (geometriesWithoutOutliers.length == 1)
      geometriesWithoutOutliers.head match {
        case geom: Polygon => geom
        case geom => geom.getEnvelope
    }
    else
      collection(geometriesWithoutOutliers).getEnvelope
  }

  def newCoordinate(x: Double, y: Double, format_yx: Boolean = false): Coordinate = {
    if (format_yx)
      new Coordinate(y, x)
    else
      new Coordinate(x, y)
  }

  def mergeLines(geom: Geometry): Geometry = {
    val lm = new LineMerger
    lm.add(geom)
    val ml = lm.getMergedLineStrings
    val geometryFactory = geom.getFactory
    geometryFactory.buildGeometry(ml)
  }

  def makePolygon(geom: Geometry): Geometry = {
    val geometryFactory = geom.getFactory
    val linearRing = geometryFactory.createLinearRing(geom.getCoordinates)
    geometryFactory.createPolygon(linearRing)
  }

  def makeLineString(coordinates: Array[Coordinate]): Geometry = {
    val geometryFactory = JTSFactoryFinder.getGeometryFactory
    geometryFactory.createLineString(coordinates)
  }


  def makePoint(x: Double, y: Double): Geometry = {
    val geometryFactory = JTSFactoryFinder.getGeometryFactory
    geometryFactory.createPoint(newCoordinate(x, y))
  }

  def orthoDistance(from: Geometry, to: Geometry): Double = {
    val calc = new GeodeticCalculator()
    calc.setStartingGeographicPoint(from.getCentroid.getX, from.getCentroid.getY)
    calc.setDestinationGeographicPoint(to.getCentroid.getX, to.getCentroid.getY)
    calc.getOrthodromicDistance
  }

  def distancePoint(geom: Geometry, distance: Double, azimuth: Double): Geometry = {
    val calc = new GeodeticCalculator()
    calc.setStartingGeographicPoint(geom.getCentroid.getX, geom.getCentroid.getY)
    calc.setDirection(azimuth, distance)
    val point2d = calc.getDestinationGeographicPoint
    makePoint(point2d.getX, point2d.getY)
  }

  def distanceArc(geom: Geometry, distance: Double, azimuth: Option[Double] = None): Geometry = {
    val (from, to, step): (Double, Double, Double) = azimuth match {
      case Some(az)=> (az - 45, az + 45, 10)
      case None => (0, 360, 10)
    }
    val distantCoordinates = for (angle <- BigDecimal(from) to BigDecimal(to) by BigDecimal(step)) yield {
      val distantPoint = distancePoint(geom, distance, angle.toDouble)
      distantPoint.getCoordinate
    }
    makeLineString(distantCoordinates.toArray)
  }

  def collection(geometries: Array[Geometry]): Geometry = {
    val factory = new GeometryFactory()
    factory.createGeometryCollection(geometries.flatMap(dumpGeometry))
  }

  def union(x: Geometry, y: Geometry): Geometry = x.union(y)

  def union(geometries: Array[Geometry]): Geometry = geometries.reduce(_.union(_))

  def buffer(geometry: Geometry, bufferValue: Double, force: Boolean = false): Geometry = geometry match {
    case geom: Polygon if !force => geom
    case geom: Geometry => geom.buffer(bufferValue)
  }

  def buffer_by_factor(geometry: Geometry, factor: Double, force: Boolean = false): Double = {
    val locationDiagonal = diagonal(geometry)
    (locationDiagonal * factor - locationDiagonal) / (4 * 100000)
  }

  def intersection(geometries: Array[Geometry]): Geometry = {
    geometries.reduce(intersection)
  }

  def intersection(x: Geometry, y: Geometry): Geometry = {
    val intersections = for{geometryX <- dumpGeometry(x)
                          geometryY <- dumpGeometry(y)} yield {
      val dump: Array[Geometry] = dumpGeometry(geometryX.intersection(geometryY)).flatMap {
        case p: Polygon => Some(p)
        case _ => None
      }
      dump
    }
    collection(intersections.flatten.filter(!_.isEmpty))
  }

  def difference(x: Geometry, y: Geometry): Geometry = {
    val differences = for{geometryX <- dumpGeometry(x)
                          geometryY <- dumpGeometry(y)} yield geometryX.difference(geometryY)
    collection(differences.filter(!_.isEmpty))
  }

  def rotate(geom: Geometry, angle: Double): Geometry = {
    val radians = angle / 360 * 2 * math.Pi
    val affineTransform = AffineTransform.getRotateInstance(radians, geom.getCentroid.getX, geom.getCentroid.getY)
    val mathTransform = new AffineTransform2D(affineTransform)
    JTS.transform(geom, mathTransform)
  }

  def translate(geom: Geometry, shiftx: Double, shifty: Double): Geometry = {
    val affineTransform = AffineTransform.getTranslateInstance(shiftx, shifty)
    val mathTransform = new AffineTransform2D(affineTransform)
    JTS.transform(geom, mathTransform)
  }

  def scale(geom: Geometry, factor: Double): Geometry = scale(geom, factor, factor)

  def scale(geom: Geometry, factorx: Double, factory: Double): Geometry = {
    // Scale geometry
    val affineTransform = AffineTransform.getScaleInstance(factorx, factory)
    val mathTransform = new AffineTransform2D(affineTransform)
    val geomScaled = JTS.transform(geom, mathTransform)
    // Move scaled geometry back to its original position
    val geomScaledCentroid = geomScaled.getCentroid
    val origCentroid = geom.getCentroid
    translate(geomScaled, origCentroid.getX - geomScaledCentroid.getX, origCentroid.getY - geomScaledCentroid.getY)
  }

  def diagonal(geom: Geometry): Double = {
    val geom_bounds = geom.getEnvelope.getCoordinates
    //if (geom_bounds.size == 5) geom_bounds(0).distance(geom_bounds(2)) else 0
    if (geom_bounds.size == 5) {
      val point1 = makePoint(geom_bounds(0).x, geom_bounds(0).y)
      val point2 = makePoint(geom_bounds(2).x, geom_bounds(2).y)
      orthoDistance(point1, point2)
    } else 0
  }

  def between(geomX: Geometry, geomY: Geometry): Geometry = {
    val coordfactory = CoordinateArraySequenceFactory.instance()
    val geomX_centroid = geomX.getCentroid
    val geomX_diagonal = diagonal(geomX)
    val geomY_centroid = geomY.getCentroid
    val geomY_diagonal = diagonal(geomY)

    // Trace a segment between the center of the polygons and get the intersection with the polygon borders
    val trace = new LineSegment(
      newCoordinate(geomX_centroid.getX, geomX_centroid.getY),
      newCoordinate(geomY_centroid.getX, geomY_centroid.getY))
      .toGeometry(geomX.getFactory)

    val orthogonal_trace = rotate(trace, 90)

    val geomX_factor = geomX_diagonal / orthogonal_trace.getLength
    val geomX_scaled_trace = scale(orthogonal_trace, geomX_factor)
    val geomX_scaled_trace_centroid = geomX_scaled_trace.getCentroid
    val geomX_trace = translate(geomX_scaled_trace, geomX_centroid.getX - geomX_scaled_trace_centroid.getX, geomX_centroid.getY - geomX_scaled_trace_centroid.getY)
    val geomX_coord = {
      val trace_intersection = geomX_trace.intersection(geomX)
      if (trace_intersection.isEmpty)
        geomX_trace.getCentroid.getCoordinates
      else
        trace_intersection.getCoordinates
    }

    val geomY_factor = geomY_diagonal / orthogonal_trace.getLength
    val geomY_scaled_trace = scale(orthogonal_trace, geomY_factor)
    val geomY_scaled_trace_centroid = geomY_scaled_trace.getCentroid
    val geomY_trace = translate(geomY_scaled_trace, geomY_centroid.getX - geomY_scaled_trace_centroid.getX, geomY_centroid.getY - geomY_scaled_trace_centroid.getY)
    val geomY_coord = {
      val trace_intersection = geomY_trace.intersection(geomY)
      if (trace_intersection.isEmpty)
        geomY_trace.getCentroid.getCoordinates
      else
        trace_intersection.getCoordinates
    }

    val coordinates = geomX_coord ++ geomY_coord.reverse
    val between_ring = if (coordinates.length < 3)
      new LineString(coordfactory.create(coordinates), geomX.getFactory)
    else
      new LinearRing(coordfactory.create(coordinates :+ geomX_coord.head), geomX.getFactory)

    if (between_ring.isClosed) {
      makePolygon(between_ring)
    } else {
      between_ring
    }

  }
}
