import numpy as np
import pandas as pd
import csv
import matplotlib.pyplot as plt
import shapefile as sf
from sklearn import metrics
from sklearn.ensemble import RandomForestRegressor
from scipy.interpolate import griddata
from mpl_toolkits.mplot3d import Axes3D


# training data are all hydromet sites + rainfall totals for all site for 10 days
# before and after every lake travis observation

class Basin:
    """
    Make a model of a river basin from historical data.  The historical data
    in this case are rainfall rates, which then predict stream flow rates,
    which then predict the elevation of a lake in the basin.  Use the
    modelHistorical() method to make this model.
    """
    def __init__( self, **kwargs ):
        self.dates = pd.date_range( kwargs[ 'startDate' ], kwargs[ 'endDate' ] )
        self.readData( **kwargs )
        #self.model( **kwargs )

    def readData( self, **kwargs ):
        # read in all the historical training data

        self.readWeather( self.dates, test = False, **kwargs )
        self.readHydro( **kwargs )
        self.readLake( **kwargs )
        self.readStationNames( **kwargs )

    def convertDate( self, inpDate ):

        months = { 'Jan': '01', 'Feb': '02', 'Mar': '03', 'Apr': '04',
                   'May': '05', 'Jun': '06', 'Jul': '07', 'Aug': '08',
                   'Sep': '09', 'Oct': '10', 'Nov': '11', 'Dec': '12'
                   }
        out = str( inpDate[ 2 ] )
        out += '-' + months[ inpDate[ 0 ] ]
        out += '-' + inpDate[ 1 ].rjust( 2, '0' )

        return out

    def readStationNames( self, **kwargs ):
        # figure out station names from their ID numbers

        stations = {}
        with open( kwargs[ 'stationNamesFile' ] ) as fp:
            for line in fp:
                ID = line.split( ',' )[ 0 ]
                name = line.split( ',') [ 1 ]
                lat = float( line.split( ',' )[ 2 ] )
                lon = float( line.split( ',' )[ 3 ] )
                stations[ ID ] = [ name, lat, lon ]

        self.stationNames = stations
                   

    def readWeather( self, dates, test = None, **kwargs ):
        # read in the rainfall data

        if test:
            filepath = kwargs[ 'testWeatherFile' ]
        else:
            filepath = kwargs[ 'weatherFile' ]
        
        stationNames = set()
        # read through the file once to get all the station names
        with open( filepath ) as fp:
            reader = csv.reader( fp )
            reader.next() # skip header
            for row in reader:
                name = row[ 0 ][ 6: ]
                stationNames.add( name )


        df = pd.DataFrame( np.nan, index = dates, columns = stationNames )
        stations = {}
        
        with open( filepath ) as fp:
            reader = csv.reader( fp )
            reader.next() # skip header
            for row in reader:
                name = row[ 0 ][ 6: ]
                date = row[ 5 ]
                rain = row[ 6 ]
                df.loc[ date, name ] = rain # pandas is cool

                if name not in stations.keys():
                    try:
                        stations[ name ] = [ float( row[ 3 ] ),
                                             float( row[ 4 ] ) ]
                    except ValueError:
                        stations[ name ] = [ np.nan, np.nan ]

        # fill missing values
        df.fillna( df.mean(), inplace = True ) # fill with station means

        # maybe get fancier and also encode the locations of the stations
        # and have scipy interpolate spatially (rather than temporally)

        if test:
            self.testWeather = df
            self.testWeatherLocs = stations
        else:
            self.weather = df
            self.weatherLocs = stations

        
    def readHydro( self, **kwargs ):
        # read in all the stream flow data
        
        stationNames = []
        stationFile = open( kwargs[ 'stationFile' ] )
        for line in stationFile:
            stationNames.append( int( line ) )
        stationFile.close()

        df = pd.DataFrame( np.nan, index = self.dates, columns = stationNames )
                           
        with open( kwargs[ 'hydroFile' ] ) as f:
            for line in f:
                tup = line.split()[ 0 ]
                
                # awkward processing of data since my Pig script outputs tuples
                # in a funny format
                stationID = int( tup.split( ',' )[ 0 ][ 1: ] )
                date = tup.split( ',' )[ 1 ][ :-1 ]
                flow = line.split()[ 1 ]
                df.loc[ date, stationID ] = flow

        # fill missing data first with previous days value
        # up to maximum of maxFill

        df.fillna( method = 'pad', limit = kwargs[ 'maxFill' ], inplace = True )
        df.fillna( df.mean(), inplace = True ) # fill remainder with station avg

        self.hydro = df.dropna( axis = 1 ) # drop stations with all nan

    def readLake( self, **kwargs ):
        
        # read data from file containing historical observations
        # of lake levels.
        
        lakeLevels = pd.DataFrame( np.nan, index = self.dates,
                                   columns = [ 'level' ] )
        lakeFile = kwargs[ 'lakeFile' ]
        with open( lakeFile ) as f:
            for line in f:
                level = float( line.split()[ 3 ] )
                date = self.convertDate( line.split()[ :3 ] )
                lakeLevels.loc[ date ] = level

        lakeLevels.fillna( method = 'pad', inplace = True )
        lakeLevels.fillna( method = 'bfill', inplace = True )
        self.lake = lakeLevels

    def getRow( self, row, target, **kwargs ):
        # reformat training data to include delay
        
        out = []
        for item in row:
            out += target[ row ].tolist()[ 0 ]

        return out

    def getStation( self, col, nDays ):
        # get station and delay from expanded training matrix

        nDays = kwargs[ 'nDays' ]
        station = col // ( nDays + 1 )
        delay = col % ( nDays + 1 ) - nDays

        return station, delay


    def setDelay( self, A, nDays ):
        # reformat training data to include station observations up to
        # nDays in the past
        
        X = np.zeros( ( A.shape[ 0 ],
                        ( nDays + 1 ) * A.shape[ 1 ] ) )
        
        for iDate in range( A.shape[ 0 ] ):
            dateRange = range( iDate - nDays, iDate + 1 )
            dateRange = [ max( date, 0 ) for date in dateRange ]
            row = self.getRow( dateRange, A )
            X[ iDate ] = row

        return X

    def modelHistorical( self, **kwargs ):
        # make model of stream flows and lake levels from historical data
        
        print 'converting rainfall to flow rates'
        self.fitFlowRates( self.weather.values, self.hydro.values, **kwargs )
        print 'converting flow rates to lake levels'
        self.fitLakeLevels( self.hydro.values, self.lake.values[ :, 0 ],
                            **kwargs )

    def fitFlowRates( self, rainData, flowData, **kwargs ):
        # model stream flows from rainfall rates

        xTrain = self.setDelay( rainData, kwargs[ 'nDays' ] )
        yTrain = flowData

        model = RandomForestRegressor( n_estimators = 50, n_jobs = 4,
                                       random_state = 42, oob_score = True )
        model.fit( xTrain, yTrain )

        self.flowModel = model

    def fitLakeLevels( self, flowData, lakeData, **kwargs ):
        # model lake levels from stream flows
        
        xTrain = self.setDelay( flowData, kwargs[ 'nDays' ] )
        yTrain = self.lake.values[ :, 0 ]
        model = RandomForestRegressor( n_estimators = 50, n_jobs = 4,
                                       random_state = 42, oob_score = True )
        
        model.fit( xTrain, yTrain )

        self.lakeModel = model
        
        ypreds = model.predict( xTrain )

        plt.clf()
        plt.plot( self.dates, yTrain, label = 'Actual' )
        plt.plot( self.dates, ypreds, label = 'Predicted' )

        plt.xlabel( 'Date' )
        plt.ylabel( 'Lake Travis Elevation (ft)' )
        plt.legend()
        plt.savefig( 'lakelevels.png' )


    def findImportantStations( self, model, k, **kwargs ):
        # identify top k stations that are most important in the fit

        important = np.argsort( model.feature_importances_ )[ ::-1 ][ :k ]
        f_getStation = np.vectorize( self.getStation )
        stations, delays = f_getStation( important, kwargs[ 'nDays' ] )

        stationNames = [ self.hydro.iloc[ :, station ].name for
                         station in stations ]

        # fix some formatting issues
        stationNames = [ str( station ).rjust( 8, '0' ) for
                         station in stationNames ]

        latlon = []
        for station in stationNames:
            try:
                latlon.append( self.stationNames[ station ] )
            except KeyError:
                pass

        # write out important stations for plotting in R
        with open( 'important_stations.id', 'w' ) as fw:
            for station in latlon:
                out = station[ 0 ] + ',' + str( station[ 1 ] ) + ','
                out += str( station[ 2 ] ) + '\n'
                fw.write( out )

        self.plotImportantStations( latlon, stations, delays, important )

    def plotImportantStations( self, names, stations, delays, important ):
        # plot feature importances 
        
        forest = self.lakeModel
        std = np.std( [tree.feature_importances_ for tree in forest.estimators_], axis = 0 )
        importances = forest.feature_importances_
        
        plt.clf()
        plt.bar( range( len( importances ) ), importances )
        plt.ylabel( 'Feature Importance' )
        plt.xlabel( 'Feature' )
        plt.savefig( 'importances.png' )

        plt.clf()
        plt.bar( range( len( important ) ),
                 forest.feature_importances_[ important ], color = 'r',
                 align = 'center' )

        plt.ylim( [ 0., 0.5 ] )
        iStation = 0
        for name in names:
            plt.text( iStation,
                      0.48,
                      name[ 0 ], rotation = 'vertical' )
            iStation += 1

        plt.xlabel( 'Station' )
        plt.ylabel( 'Station Importance' )
        plt.savefig( 'important_stations.png' )


    def predict( self, **kwargs ):
        self.modelHistorical( **kwargs )

        self.testDates = pd.date_range( kwargs[ 'testStartDate' ],
                                        kwargs[ 'testEndDate' ] )

        self.readWeather( self.testDates, test = True, **kwargs )
        self.interpolateTestWeather( **kwargs )

        # use fitted model to predict new flows and lake levels
        self.predFlowRates( **kwargs ) 
        self.predLakeLevels( **kwargs )

    def interpolateTestWeather( self, **kwargs ):

        df = pd.DataFrame( np.nan, index = self.testDates,
                           columns = self.weather.columns )

        # take intersection
        common = self.weather.columns & self.testWeather.columns
        # if actual station exists in 1991 set, use its data
        df[ common ] = self.testWeather[ common ] 

        # remaining stations need to be interpolated
        remaining = self.weather.columns - common

        xyTest = self.testWeatherLocs.values()
        xyTrain = self.weatherLocs.values()

        # funny indexing to keep in same order as dict
        zTest = self.testWeather[ self.testWeatherLocs.keys() ].values

        for key in remaining:
            entry = []
            for day in range( zTest.shape[ 0 ] ):
                entry += griddata( xyTest, zTest[ day, : ],
                                   [ self.weatherLocs[ key ] ] ).tolist() 
            df[ key ] = entry

        df.fillna( method = 'pad', inplace = True )
        df.fillna( method = 'bfill', inplace = True )
        df.fillna( value = 0., inplace = True )

        self.testWeather = df # overwrite previous with interpolated

    def predFlowRates( self, **kwargs ):

        print 'predicting new flow rates'
        
        nDays = kwargs[ 'nDays']
        model = self.flowModel
        xTest = self.setDelay( self.testWeather.values, nDays )
        yTest = model.predict( xTest )
        self.testFlows = yTest

    def predLakeLevels( self, **kwargs ):

        print 'predicting new lake levels'

        nDays = kwargs[ 'nDays' ]
        model = self.lakeModel
        xTest = self.setDelay( self.testFlows, nDays )
        yTest = model.predict( xTest )

        import pdb; pdb.set_trace()

        
        

    
    


def main( **kwargs ):

    colorado = Basin( **kwargs )
    colorado.predict( **kwargs )
    #colorado.modelHistorical( **kwargs )
    #colorado.findImportantStations( colorado.lakeModel, 10, **kwargs )
    import pdb; pdb.set_trace()

    
    
    

if __name__ == '__main__':
    kwargs = { 'lakeFile': '/Users/jardel/blog/drought/travis_levels.dat',
               'weatherFile': '/Users/jardel/blog/drought/noaa.weather.raw',
               'hydroFile': '/Users/jardel/blog/drought/usgs.dailyaverages/output',
               'stationFile': '/Users/jardel/blog/drought/stations.list',
               'stationNamesFile': '/Users/jardel/blog/drought/stations.latlon',
               'startDate': '2011-01-01',
               'endDate': '2012-12-31',
               'nDays': 5,
               'maxFill': 5,
               'testWeatherFile': '/Users/jardel/blog/drought/noaa.weather.test',
               'testStartDate': '1991-12-18',
               'testEndDate': '1991-12-23'
               }
    main( **kwargs )
