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


for market in marketDict:
    X = df.loc[ marketDict[ market ], : ].values
    means = np.mean( X, axis = 0 )
    norm = means[ 0 ]
    means /= norm
    plt.plot( x, means, label = marketNames[ market ] )

plt.ylim( [ 0., 1.2 ] )

plt.legend( loc = 'lower right' )
plt.show()

"""means = np.mean( X, axis = 0 )
plt.plot( x, means, 'k' )
plt.plot( x, df.loc[ 9774, : ], 'r' )


"""

"""
for dealer in dealerIDs:
    y = df.loc[ dealer, : ]
    y /= np.mean( y )
    plt.plot( x, y )
"""    

#plt.show()
    
    




#plt.plot( month, volume )
#plt.show()

