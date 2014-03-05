import numpy as np
import sqlite3 as sql
import matplotlib.pyplot as plt
import pandas as pd
import csv

conn = sql.connect( 'subset.sql' )
cursor = conn.cursor()
query = """SELECT COUNT( dealer_id ), CAST( STRFTIME( '%m', ro_close_date )
                   AS integer ) AS month FROM orders
                   GROUP BY month;"""

cursor.execute( query )
res = cursor.fetchall()
res = np.array( res )
month = res[ :, 1 ]
volume = res[ :, 0 ]

plt.clf()
plt.plot( month, volume )
plt.show()

query = """SELECT dealer_id, COUNT(*),
              CAST( STRFTIME( '%m', ro_close_date ) AS integer ) AS month
              FROM orders GROUP BY  month, dealer_id;"""
cursor.execute( query )
res = cursor.fetchall()
dealerIDs = set()
for line in res:
    dealerIDs.add( line[ 0 ] )

dealerIDs = list( dealerIDs )

df = pd.DataFrame( np.nan, index = dealerIDs, columns = range( 1, 13 ) )
for line in res:
   df.loc[ line[ 0 ], line[ 2 ] ] = line[ 1 ]

df.fillna( df.mean(), inplace = True )

X = df.values
x = range( 1, 13 )

marketDict = { 0:[], 1:[], 2:[], 3:[], 4:[] }

with open( 'market_segs.out' ) as fp:
    reader = csv.reader( fp )
    for row in reader:
        dealer = int( row[ 0 ] )
        market = int( row[ 3 ] )
        marketDict[ market ].append( dealer )

marketNames = { 0: 'Midwest', 1: 'West', 2: 'Southwest',
                3: 'Northeast', 4: 'Southeast' }

colors = [ 'red', 'purple', 'blue', 'yellow', 'green' ]

for market in marketDict:
    X = df.loc[ marketDict[ market ], : ].values
    means = np.mean( X, axis = 0 )
    norm = means[ 0 ]
    means /= norm
    plt.plot( x, means, label = marketNames[ market ], color = colors[ market ] )

plt.ylim( [ 0., 1.2 ] )
plt.ylabel( 'Sales (normalized)' )
plt.xlabel( 'Month' )
bad = c( 10467, 7437, 9894, 10728, 15948 )
data = read.csv( 'market_segs.out' )
names( data ) <- c( "dealerID", "lat", "lon", "Market" )
data[ data$dealerID %in% bad, 2:3 ] = NA
dealers = data

dealers$Market[ dealers$Market == 0 ] = "Midwest"
dealers$Market[ dealers$Market == 1 ] = "West"
dealers$Market[ dealers$Market == 2 ] = "Southwest"
dealers$Market[ dealers$Market == 3 ] = "Northeast"
dealers$Market[ dealers$Market == 4 ] = "Southeast"

baseMap <- get_map( location = c( lon = -96.78, 38.37 ),
                        maptype="hybrid", source="google", zoom = 4)

map = ggmap( baseMap ) + geom_point( aes( x = lon, y = lat,
  color = factor( Market ) ),  data = dealers ) + xlab( "" ) + ylab("")x

ggsave( map, file = "map.png" )


plt.legend( loc = 'lower right' )
plt.savefig( 'market_time.png' )

