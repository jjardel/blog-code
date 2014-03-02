import numpy as np
import pandas as pd
import sqlite3 as sql
import csv
from sklearn.cluster import MiniBatchKMeans
from sklearn.preprocessing import MinMaxScaler

# read in aggregate data on each dearlership from DB.  Then cluster the 96
# dealership points in that N-dimensional space.

class Model:
    def __init__( self, **kwargs ):
        self.readData( **kwargs )

    def readData( self, **kwargs ):
        # read in data from SQL DB to a pandas data frame
        path = kwargs[ 'pathToDB' ]
        conn = sql.connect( path )
        cursor = conn.cursor()

        query = """SELECT dealer_id, num_ROs, sales, efficiency, outOfWarrantyFraction,
                           quarterly_growth FROM metric1;"""
        cursor.execute( query )
        res = cursor.fetchall()
        res = np.array( res )

        tmp = res[ :, 0 ]
        dealerIDs = [ int( x ) for x in tmp ]
        df = pd.DataFrame( np.nan, index = dealerIDs,
                           columns = [ "volume", "sales", "efficiency", "outOfWarranty",
                                       "growth", "marketAffluence", "primaryMake" ] )
        df.iloc[ :, :5 ] = res[ :, 1: ]

        # Fill up a dictionary containing median household income for each zip code
        zipDict = {}
        path = kwargs[ 'pathToZIPFile' ]
        with open( path, 'rU' ) as fp:
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
            if dealer in df.index: # some dealers get dropped out of metric1?
                df.loc[ int( dealer ), 'marketAffluence' ] = \
                    marketAffluence[ dealer ][ 0 ]

        # get most serviced make for each dealer
        query = """SELECT dealer_id, make_Name from (select max(theCount),
                      dealer_ID, make_Name FROM
                    (select dealer_ID, count(make_name) AS theCount, make_name from
                    orders GROUP BY dealer_id, make_name)
                    GROUP BY dealer_ID)
                    GROUP BY dealer_ID;"""
        cursor.execute( query )
        res = cursor.fetchall()
        makeDict = { "NISSAN": 0, "INFINITI": 1 }

        for item in res:
            dealer = item[ 0 ]
            make = item[ 1 ]
            if dealer in df.index:
                if make in makeDict:
                    df.loc[ dealer, "primaryMake" ] = makeDict[ make ]
                else:
                    df.loc[ dealer, "primaryMake" ] = 3
                
        self.data = df

    def cluster( self, nClusters ):
        data = self.data.values
        
        # feature scaling
        scaler = MinMaxScaler()
        X = scaler.fit_transform( data )
        
        kmeans = MiniBatchKMeans( nClusters, n_init = 50 )
        kmeans.fit( X )

        import pdb; pdb.set_trace()
        

def main( **kwargs ):
    model = Model( **kwargs )
    model.cluster( 3 )
    import pdb; pdb.set_trace()

if __name__ == '__main__':
    kwargs = { 'pathToDB': 'subset.sql',
               'pathToZIPFile': 'MedianZIP.csv'
               }
    main( **kwargs )



         
    
    








