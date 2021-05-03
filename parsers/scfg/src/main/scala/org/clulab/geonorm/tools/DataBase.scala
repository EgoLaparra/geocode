package org.clulab.geonorm.tools

import org.geotools.data.simple.{SimpleFeatureCollection, SimpleFeatureStore}
import org.geotools.data._
import org.geotools.data.collection.ListFeatureCollection
import org.geotools.factory.CommonFactoryFinder
import org.geotools.feature.simple.SimpleFeatureBuilder
import org.geotools.filter.text.cql2.CQL
import org.locationtech.jts.geom.Geometry

import scala.collection.JavaConverters._


class DataBase(tableName: String = "default") {

  private val params = Map(
    "dbtype" -> "postgis",
    "port" -> 5432,
    "schema" -> "public",
    "host" -> "localhost",
    "database" -> "geometries",
    "user" -> "guest",
    "passwd" -> "guest"
  ).asJava

  private val dataStore: DataStore = DataStoreFinder.getDataStore(params)
  private val inputName = "geometries"
  private val source = dataStore.getFeatureSource(inputName)
  private val sourceSchema = source.getSchema
  private val outputName = tableName
  private val target = dataStore.getFeatureSource(outputName)
  private val targetSchema = target.getSchema
  private val ff = CommonFactoryFinder.getFilterFactory
  private val featureSource = dataStore.getFeatureSource(targetSchema.getName.getLocalPart)


  def query(osm_id: String, osm_type: String): Geometry = {
    query(Array((osm_id, osm_type))).head
  }

  def query(keyArray: Array[(String, String)]): Array[Geometry] = {
    val keySet = keyArray.map(key => ff.featureId(s"geometries.${key._1}.${key._2}")).toSet.asJava
    val filter = ff.id(keySet)
    val query = new Query(sourceSchema.getTypeName, filter)
    val feats = source.getFeatures(query).features
    val geometries = scala.collection.mutable.ListBuffer.empty[Geometry]
    while (feats.hasNext) {
      geometries.append(feats.next().getProperty("geom").getValue.asInstanceOf[Geometry])
    }
    feats.close()
    geometries.toArray
  }

  def insert(key: String, geometry: Geometry): Unit = {
    val transaction = new DefaultTransaction("create")
    featureSource match {
      case featureStore: SimpleFeatureStore =>
        featureStore.setTransaction(transaction)
        try {
          val featureBuilder = new SimpleFeatureBuilder(targetSchema)
          featureBuilder.add(key)
          featureBuilder.add(geometry)
          val feature = featureBuilder.buildFeature(s"${targetSchema.getName}.$key")
          val collection: SimpleFeatureCollection = new ListFeatureCollection(targetSchema, Array(feature))
          val ids = featureStore.addFeatures(collection)
          transaction.commit()
        } catch {
          case e: Throwable => {
            e.printStackTrace()
            transaction.rollback()
          }
        } finally {
          transaction.close()
        }
      case _ =>
        println("Database not writable")
        dataStore.dispose()
    }
  }

  def exists(key: String): Boolean = {
    val filter = CQL.toFilter(s"entity_id = '$key'")
    val query = new Query(targetSchema.getTypeName, filter)
    val feats = target.getFeatures(query).features
    val featExists = feats.hasNext
    feats.close()
    featExists
  }

  def close(): Unit = {
    dataStore.dispose()
  }
}
