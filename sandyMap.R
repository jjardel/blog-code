
library( ggmap )
library(ggplot2)
library(scales)
library( maptools )
library( RColorBrewer )
library( plyr )


args <- commandArgs( TRUE )
#args = c( "income.csv", "income" )
filename = args[ 1 ]
title = args[ 2 ]

# read zip code boundaries
zipCode.areas <- readShapePoly( 'new_jersey_zcta_shapefile.shp',
                               IDvar = "ZCTA5CE10" )
zipCode.points <- fortify( zipCode.areas )

# read plotting data
data = read.csv( filename )
names( data )[ 1 ] = "id"
zipCode.points$id = as.numeric( zipCode.points$id )

# join the zip code boundaries and the plotting data
zipCode.df = join( zipCode.points, data, type = "left", by = "id" )
zipCode.df$color = as.character( zipCode.df$color )

cols = c( '#FFFFFF', '#FFFFB2', '#FECC5C', '#FD8D3C', '#F03B20', '#BD0026' )

# get the base map from google maps
baseMap <- get_map( location = c( -75.5598, 38.92437, -73.89399, 41.3574 ),
                   color = "color", source = "google", zoom = 8 )
# over plot my fills
ggmap( baseMap ) + geom_polygon( aes( x = zipCode.df$long, y = zipCode.df$lat,
                                     group = zipCode.df$id ),
                                     fill = zipCode.df$color,
                                data = zipCode.df, color = NA, alpha = 0.5 ) +
  xlab( "" ) + ylab( "" ) + ggtitle( title ) 
  

ggsave( 'nj.png' )


