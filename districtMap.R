library(ggmap)
library(ggplot2)
library(scales)

args <- commandArgs( TRUE )

filename = args[ 1 ]

district.data <- read.csv( filename )

# determine lat/lon range to map
xcen = mean( district.data$Longitude )
ycen = mean( district.data$Latitude )

x1 = min( district.data$Longitude )
x2 = max( district.data$Longitude )
y1 = min( district.data$Latitude )
y2 = max( district.data$Latitude )

deltaX = .3 * abs( x2 - x1 )
deltaY = .3 * abs( y2 - y1 )

duplist = duplicated( district.data )
endpoints = which( duplist %in% TRUE )
nSegments = length( endpoints )

# grab the base map from google maps
district.map <- get_map( location =
                        c( x1 - deltaX, y1 - deltaY, x2 + deltaX, y2 + deltaY),
                        maptype="hybrid", source="google")

map = ggmap( district.map )
iStart = 1

# loop through the number of segments to draw the boundaries properly
for( i in 1:nSegments ){
  map = map + geom_path(
    data=district.data[ c( iStart:endpoints[ i ] ), ],
    aes(x=Longitude, y=Latitude), size = 2 )
  iStart = endpoints[ i ] + 1

}
outfile = substr( filename, 1, nchar( filename ) - 11 )
ggsave( paste( outfile, 'png', sep = '.' ) )

#print( map )
