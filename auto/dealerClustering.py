import numpy as np
import pandas as pd
import sqlite3 as sql
import csv

# read in aggregate data on each dearlership from DB.  Then cluster the 96
# dealership points in that N-dimensional space.

# engineer a feature that is max( count( make_name ) )

conn = sql.connect( 'subset.sql' )
cursor = conn.cursor()

query = """SELECT dealer_id, make_Name from (select max(theCount),
              dealer_ID, make_Name FROM
            (select dealer_ID, count(make_name) AS theCount, make_name from
            orders GROUP BY dealer_id, make_name)
            GROUP BY dealer_ID)
            GROUP BY dealer_ID;"""
cursor.execute( query )
res = cursor.fetchall()

query = """SELECT dealer_id, num_ROs, sales, efficiency, outOfWarrantyFraction,
                   quarterly_growth FROM metric1;"""
cursor.execute( query )
res = cursor.fetchall()
res = np.array( res )

tmp = res[ :, 0 ]
dealerIDs = [ int( x ) for x in tmp ]
df = pd.DataFrame( np.nan, index = dealerIDs,
                   columns = [ "volume", "sales", "efficiency", "outOfWarranty",
                               "growth", "marketAffluence" ] )
df.iloc[ :, :5 ] = res[ :, 1: ]

# Fill up a dictionary containing median household income for each zip code
zipDict = {}
with open( 'MedianZIP.csv', 'rU' ) as fp:
    reader = csv.reader( fp )
    reader.next()
    for row in reader:
        zipDict[ row[ 0 ].rjust( 5, '0' ) ] = float( row[ 1 ] )
medianIncome = np.median( zipDict.values() )

# calculate mean household income from each dealership's market
query = """SELECT dealer_id, zip FROM orders;"""
cursor.execute( query )
orderZips = cursor.fetchall()

# make a dictionary holding the average income of each dealer's market
marketAffluence = {}

for item in orderZips:
    zipcode = item[ 1 ][ :5 ] # only take 5-digit zip
    if zipcode in zipDict: # only use zips we have data for
        dealer = item[ 0 ]
        if dealer in marketAffluence:
            # calculate running average
            N = marketAffluence[ dealer ][ 1 ]
            tmp = marketAffluence[ dealer ][ 0 ] * N
            tmp += zipDict[ zipcode ]
            tmp /= ( N + 1 )
            marketAffluence[ dealer ] = [ tmp, N + 1 ]
        else:
            # insert for the first time
            marketAffluence[ dealer ] = [ zipDict[ zipcode ], 1 ]

# put it in the dataframe
for dealer in marketAffluence:
    if dealer in df: # some dealers get dropped out of metric1?
        df.loc[ int( dealer ), 'marketAffluence' ] = marketAffluence[ dealer ][ 0 ]

    
    








