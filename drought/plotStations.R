library( ggmap )
library(ggplot2)
library(scales)
library( maptools )
library(RColorBrewer)
library( grid )


baseMap <- get_map( location = c( lon = -99.202608, lat = 30.986881 ),
                        maptype="hybrid", source="google", zoom = 7)

rivers = readShapeLines( 'tceq_segments/TCEQ_SEGMENTS_LINE_2012' )
colorado = subset( rivers, rivers$BASIN_NAME == 'Colorado River Basin' )
colorado.lines = fortify( colorado )

bigRivers = readShapeLines( 'basins/basins_dd' )
bigRivers.colorado = subset( bigRivers, bigRivers$BASIN_NAME == 'Colorado' )
bigRivers.lines = fortify( bigRivers.colorado )

lakes = readShapePoly( 'texas_water' )
#LCRA = subset( lakes, lakes$NAME == 'Lake Travis' | lakes$NAME == 'Lake Buchanan' )
lakes.lines = fortify( lakes )

# read important stations

stations = read.csv( 'important_stations.id', header = FALSE )
names( stations ) = c( 'name', 'lat', 'long' )
stations$rank = as.numeric( rownames( stations ) )

# play with the justification

left = subset( stations, stations$rank %in% c( 4, 2, 8, 6 ) )
right = subset( stations, stations$rank %in% c( 3, 1, 7, 5 ) )

# arrow to point at lake travis
arrow1 = data.frame( y = 30.176858, x = -98.089149, dx = 0.05, dy = 0.05 )



map = ggmap( baseMap ) + geom_polygon(aes(x = long,
  y = lat,  group = group),  data = lakes.lines,  color = '#42C0FB',
  alpha = 0.5) +  labs(x = "", y = "") +
  geom_path(aes(x = long, y = lat,  group = group), data = colorado.lines,
            color = '#42C0FB', alpha = 0.5) +
geom_path(aes(x = long, y = lat,  group = group), data = bigRivers.lines,
          color = '#42C0FB',  alpha = 0.5) +
geom_point( aes( x = long, y = lat ), data = stations ) +
  geom_text( aes( x = long, y = lat, label = name, hjust = 1 ),
            data = left, size = 3, angle = 0, fontface = 'bold' ) +
  geom_text( aes( x = long, y = lat, label = name, hjust = 0 ),
            data = right, size = 3, angle = 0, fontface = 'bold' ) +
   geom_segment( aes( x =-97.597904, y = 31.592574, yend = 30.522047,
                     xend = -98.058901 ), arrow = arrow( ends = "last" ),
                     size = 1, color = 'black' ) +
  geom_text( aes( x =-97.597904, y = 31.702574, label = 'Lake Travis' ),
            size = 5, fontface = 'bold' )

ggsave( 'important_stations.png' )
print( map )



#lines.2 <- spTransform(lines, CRS("+proj=longlat +datum=WGS84"))
