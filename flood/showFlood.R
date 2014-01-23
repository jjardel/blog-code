library( ggplot2 )
library( ggmap )
library(scales)
library( maptools )
library(RColorBrewer)
library( grid )

flood = read.csv( 'rainfall.out' )
names( flood ) = c( 'lat', 'lon', 'rain' )

baseMap <- get_map( location = c( lon = -99.202608, lat = 30.986881 ),
                        maptype="hybrid", source="google", zoom = 7)

# add minor rivers
rivers = readShapeLines( 'tceq_segments/TCEQ_SEGMENTS_LINE_2012' )
colorado = subset( rivers, rivers$BASIN_NAME == 'Colorado River Basin' )
colorado.lines = fortify( colorado )

# add major rivers
bigRivers = readShapeLines( 'basins/basins_dd' )
bigRivers.colorado = subset( bigRivers, bigRivers$BASIN_NAME == 'Colorado' )
bigRivers.lines = fortify( bigRivers.colorado )

# add lakes
lakes = readShapePoly( 'texas_water' )
lakes.lines = fortify( lakes )

# color scale
breaks <- seq(min(flood$rain) * 0.95, max(flood$rain) * 1.05, length = 21)
col <- rev(heat.colors(20))

theLabels <- round(breaks, 2)
indLabels <- floor(seq(1, length(theLabels), length.out = 5))
indLabels[length(indLabels)] <- length(theLabels)
theLabels <- as.character(theLabels[indLabels])
theLabels[theLabels == "0"] <- " 0.00 "


# the map
map = ggmap( baseMap ) +
  geom_polygon(aes(x = long, y = lat,  group = group),
               data = lakes.lines, color = 'blue', alpha = 0.4 ) +
  labs(x = "", y = "") +
  geom_path(aes(x = long, y = lat,  group = group),
            data = colorado.lines, color = 'blue', alpha = 0.4 ) +
  geom_path(aes(x = long, y = lat,  group = group),
            data = bigRivers.lines, color = 'blue',  alpha = 0.4 ) +
  stat_contour( data = flood, geom = "polygon",
               aes( x = lon, y = lat, z = rain, fill = ..level.. ),
               alpha = 0.08, bins = 15 ) +
  scale_fill_gradient( name = "Rainfall (inches)", low = "white",
                        high = "blue", breaks = breaks[ indLabels ],
                        limits = range( breaks ), labels = theLabels )

ggsave( 'rainfall_amount.png' )
print( map )
