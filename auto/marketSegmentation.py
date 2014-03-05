import numpy as np
import pandas as pd
import sqlite3 as sql
import matplotlib.pyplot as plt
import csv
from sklearn.cluster import KMeans
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import silhouette_score

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

        # Fill up a dictionary containing lat/long of every zip code
        zipDict = {}
        path = kwargs[ 'pathToZIPFile' ]
        with open( path, 'rU' ) as fp:
            reader = csv.reader( fp )
            reader.next()
            for row in reader:
                try:
                    lat = float( row[ 3 ] )
                    lon = float( row[ 4 ] )
                    zipDict[ row[ 2 ].rjust( 5, '0' ) ] = [ lat, lon ]
                except:
                    # bad formatting in this big file
                    pass
                    

        # estimate rough dealer location as the lat/long center of all its ROs
        query = """SELECT dealer_id, zip FROM orders;"""
        cursor.execute( query )
        orderZips = cursor.fetchall()

        dealerLocations = {}
        # dict with [ latCen, lonCen, nOrders ] as value
        
        for item in orderZips:
            zipcode = item[ 1 ][ :5 ] # only take 5-digit zip
            if zipcode in zipDict :# only use zips we have data for
                dealer = item[ 0 ]
                if dealer in dealerLocations:
                    # calculate running average of lat/long
                    N = dealerLocations[ dealer ][ 2 ]
                    tmpLat = dealerLocations[ dealer ][ 0 ] * N
                    tmpLat += zipDict[ zipcode ][ 0 ]
                    tmpLat /= ( N + 1 )
                    tmpLon = dealerLocations[ dealer ][ 1 ] * N
                    tmpLon += zipDict[ zipcode ][ 1 ]
                    tmpLon /= ( N + 1 )
                    dealerLocations[ dealer ] = [ tmpLat, tmpLon, N + 1 ]
                else:
                    #insert for the first time
                    dealerLocations[ dealer ] = zipDict[ zipcode ] + [ 1 ]

        self.geoData = dealerLocations

    def findBestClustering( self, maxClusters = 10 ):
        
        locs = self.geoData
        lats = [ locs[ dealer ][ 0 ] for dealer in locs ]
        lons = [ locs[ dealer ][ 1 ] for dealer in locs ]

        X = np.column_stack( ( lats, lons ) )

        cost = []
        score = []
        for nClusters in range( 2, maxClusters ):
            clustering, inertia, silhouette = self.cluster( nClusters, X )
            cost.append( inertia )
            score.append( silhouette )

        plt.plot( range( 2, maxClusters ), cost )
        plt.show()
        
        
    def cluster( self, nClusters, X ):
        
        kmeans = KMeans( nClusters, n_init = 50, n_jobs = -1, random_state = 42 )
        kmeans.fit( X )
        labels = kmeans.labels_
        inertia = kmeans.inertia_
        score = silhouette_score( X, labels, metric = 'euclidean' )

        print nClusters, 'inertia = ', inertia, 'silhouette score = ', score

        return labels, inertia, score

    def writeSegments( self, nClusters ):

        locs = self.geoData
        lats = [ locs[ dealer ][ 0 ] for dealer in locs ]
        lons = [ locs[ dealer ][ 1 ] for dealer in locs ]
        dealers = locs.keys()

        data = np.column_stack( ( lats, lons ) )
        
        labels, inertia, score = self.cluster( nClusters, data )
        
        out = np.array( zip( dealers, lats, lons, labels ) )
        np.savetxt( 'market_segs.out', out, fmt = '%i,%f,%f,%i' )
        
    

def main( **kwargs ):
    model = Model( **kwargs )
    #model.findBestClustering()
    model.writeSegments( nClusters = 5 )
    import pdb; pdb.set_trace()

if __name__ == '__main__':
    kwargs = { 'pathToDB': 'subset.sql',
               'pathToZIPFile': 'cityzip.csv'
               }
    main( **kwargs )



         
    
    








