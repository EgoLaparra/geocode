organization := "org.clulab"
name := "geonorm"
version := "1.0.5"

scalaVersion := "2.12.8"
crossScalaVersions := List("2.11.12", "2.12.8", "2.13.0")
scalacOptions := Seq("-unchecked", "-deprecation")


resolvers ++= Seq(
  "maven2-repository.dev.java.net" at "https://download.java.net/maven/2",
  "osgeo" at "https://repo.osgeo.org/repository/release/",
  "boundless" at "https://repo.boundlessgeo.com/main",
)


libraryDependencies ++= {
  val geotoolsVersion = "23.0"

  Seq(
    "commons-io"                % "commons-io"          % "2.6",
    "org.slf4j"                 % "slf4j-nop"           % "1.6.4",
    "org.scala-lang.modules"    %% "scala-xml"          % "1.0.6",
    "org.geotools"              % "gt-shapefile"        % geotoolsVersion,
    "org.geotools"              % "gt-swing"            % geotoolsVersion,
    "org.geotools"              % "gt-epsg-hsql"        % geotoolsVersion,
    "org.geotools"              % "gt-geotiff"          % geotoolsVersion,
    "org.geotools"              % "gt-tile-client"      % geotoolsVersion,
    "org.geotools"              % "gt-opengis"          % geotoolsVersion,
    "org.geotools"              % "gt-process-feature"  % geotoolsVersion,
    "org.geotools.jdbc"         % "gt-jdbc-postgis"     % geotoolsVersion,
    "org.locationtech.jts"      % "jts-core"            % "1.16.1",
    "junit"                     % "junit"               % "4.12" % Test,
    "org.scalatest"             %% "scalatest"          % "3.0.8" % Test,
    "com.lexicalscope.jewelcli"  % "jewelcli"           % "0.8.9" % Test,
  )
}

mainClass in (Compile, packageBin) := Some("org.clulab.timenorm.scate.TemporalNeuralParser")

Test / fork := true

// Additional metadata required by Sonatype OSS
// https://www.scala-sbt.org/1.x/docs/Using-Sonatype.html
organizationName := "computational language understanding lab"
organizationHomepage := Some(url("http://clulab.org/"))

scmInfo := Some(
  ScmInfo(
    url("https://github.com/EgoLaparra/geonorm/"),
    "scm:git@github.com:EgoLaparra/timenorm.git"
  )
)
developers := List(
  Developer(
    id    = "EgoLaparra",
    name  = "Egoitz Laparra",
    email = "laparra@email.arizona.edu",
    url   = url("http://clulab.cs.arizona.edu/people.php")
  ),
)

description := "Reads and converts complex descriptions of geolocations to their geometry."
licenses := List("Apache 2" -> new URL("http://www.apache.org/licenses/LICENSE-2.0.txt"))
homepage := Some(url("https://github.com/example/project"))

// Remove all additional repository other than Maven Central from POM
pomIncludeRepository := { _ => false }
