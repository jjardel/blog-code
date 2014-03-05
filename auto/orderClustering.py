import numpy as np
import pandas as pd
import sqlite3 as sql
import matplotlib.pyplot as plt
import csv
from sklearn.cluster import MiniBatchKMeans
from sklearn.preprocessing import MinMaxScaler
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score

class Model:
    """
    Clustering model for all ROs.  Splits ROs into two classes based on
    the mileage of the car, cost of the repair, and length of labor time.
    It turns out these clusters are good definitions for maintenance service
    or major repairs

    """
    def __init__( self, **kwargs ):
        pathToDB = kwargs[ 'pathToDB' ]
        
        self.readROs( pathToDB )
        self.cluster( 2 )
        self.calcOrderTypes( pathToDB )
        self.findMake( pathToDB )
        

    def readROs( self, dbPath ):
        conn = sql.connect( dbPath )
        cursor = conn.cursor()
        query = """ SELECT dealer_id, Mileage, 
                    Customer_Total + Warranty_Total + Internal_Total AS sales,
                    Labor_Time FROM orders WHERE Mileage != '' """
        cursor.execute( query )
        res = cursor.fetchall()
        tmp = np.array( res )
        self.orders = np.array( res, dtype = 'float' )[ :, 1: ]
        self.dealers = [ int( x ) for x in tmp[ :, 0 ] ]
        conn.close()

    def calcOrderTypes( self, dbPath ):

        # initialize dictionary with order types
        orderTypes = {}
        for dealer in set( self.dealers ):
            orderTypes[ dealer ] = [ 0, 0 ]

        for record in zip( self.dealers, self.labels, self.orders[ :, 1 ] ):
            #orderTypes[ record[ 0 ] ][ record[ 1 ] ] += record[ 2 ]
            orderTypes[ record[ 0 ] ][ record[ 1 ] ] += 1

        ins = []
        for dealer in orderTypes:
            total = float( sum( orderTypes[ dealer ] )  )
            fracMaintenance = orderTypes[ dealer ][ 0 ] / total
            fracRepairs = orderTypes[ dealer ][ 1 ] / total
            ins.append( ( dealer, fracMaintenance, fracRepairs ) )

        # insert into SQL DB
        conn = sql.connect( dbPath )
        cursor = conn.cursor()
            
        statement = """DROP TABLE IF EXISTS orderTypes"""
        cursor.execute( statement )
        
        statement = """CREATE TABLE orderTypes
                     (dealer_id integer, fracMaintenance float,
                     fracRepairs float ); """
        cursor.execute( statement )

        statement = """INSERT INTO orderTypes VALUES (?,?,?);"""
        cursor.executemany( statement, ins )
        conn.commit()
        conn.close()

        ins = np.array( ins )
        np.savetxt( 'orderTypes.out', ins, fmt = '%i,%f,%f' )
        self.orderTypes = orderTypes

    def findMake( self, pathToDB ):
        
        conn = sql.connect( pathToDB )
        cursor = conn.cursor()
        
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
                    df.loc[ dealer, "primaryMake" ] = 2

        makes = df.loc[ :, "primaryMake" ].values
        dealers = df.index
        ins = zip( dealers, makes )
        np.savetxt( 'makes.out', ins, fmt = '%i,%i' )
            

    def findBestClustering( self, maxClusters = 10 ):
        # no longer needed
        
        cost = []
        score = []
        for nClusters in range( 2, maxClusters ):
            clustering, silhouette = self.cluster( nClusters )
            cost.append( clustering.inertia_ )
            score.append( silhouette )

        plt.plot( range( 2, maxClusters ), cost )
        plt.show()
        
        import pdb; pdb.set_trace()
        
        
    def cluster( self, nClusters ):

        # run k-means clustering to cluster all ROs into two classes according
        # to the mileage of the car, cost of the repair, and labor time
        
        data = self.orders
        # feature scaling
        scaler = StandardScaler()
        X = scaler.fit_transform( data )
        kmeans = MiniBatchKMeans( nClusters, n_init = 1000, batch_size = 100000,
                                  random_state = 42 )
        kmeans.fit( X )
        labels = kmeans.labels_

        print 'CLUSTER CENTERS AT '
        print kmeans.cluster_centers_

        score = silhouette_score( X, labels, metric = 'euclidean', sample_size = 10000 )
        print 'AVERAGE SILHOUETTE SCORE ', score

        self.labels = labels

def main( **kwargs ):
    model = Model( **kwargs )

if __name__ == '__main__':
    kwargs = { 'pathToDB': 'subset.sql'
               }
    main( **kwargs )



         
    
    








