import numpy as np
import pandas as pd
import csv
import matplotlib.pyplot as plt
import shapefile as sf
from sklearn import metrics
from sklearn.ensemble import ExtraTreesRegressor
from mpl_toolkits.mplot3d import Axes3D
from sklearn.linear_model import RidgeCV
from sklearn import preprocessing


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

        print 'reading training data'
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
        # read in the rainfall data for either training case or test case

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

        if test:
            stationNames = self.weather.columns # use same stations as training

        df = pd.DataFrame( np.nan, index = dates, columns = stationNames )
        stations = {}
        
        with open( filepath ) as fp:
            reader = csv.reader( fp )
            reader.next() # skip header
            for row in reader:
                name = row[ 0 ][ 6: ]
                date = row[ 5 ]
                rain = row[ 6 ]
                if date in dates:
                    if not test or ( test and name in stationNames ):
                        df.loc[ date, name ] = rain # pandas is cool
                    
                if name not in stations.keys():
                    try:
                        stations[ name ] = [ float( row[ 3 ] ),
                                             float( row[ 4 ] ) ]
                    except ValueError:
                        stations[ name ] = [ 0., 0. ]

        # fill missing values
        threshold = kwargs[ 'completenessThreshold' ]
        nExamples = df.shape[ 0 ]
        nGood = df.count()
        completeness = nGood / float( nExamples )

        # drop stations with too many missing values
        if not test:
            dropList = completeness[ completeness < threshold ].index.tolist()
            df = df.drop( dropList, axis = 1  )

        # fill forward up to a limit
        df.fillna( method = 'pad', limit = kwargs[ 'maxFill' ], inplace = True )

        # clobber the rest with zeros
        df.fillna( value = 0., inplace = True )

        
        """
        df.fillna( df.mean(), inplace = True ) # fill with station means
        df.fillna( value = 0., inplace = True ) # clobber remaining with zeros
        """
                        
        # maybe get fancier and also encode the locations of the stations
        # and have scipy interpolate spatially (rather than temporally)

        if test:
            self.testWeather = df
            self.testWeatherLocs = stations
        else:
            self.weather = df
            self.weatherLocs = stations

            print 'done weather data'

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

        # fill missing data
                
        threshold = kwargs[ 'completenessThreshold' ]
        nExamples = df.shape[ 0 ]
        nGood = df.count()
        completeness = nGood / float( nExamples )

        # drop stations with too many missing values
        dropList = completeness[ completeness < threshold ].index.tolist()
        df = df.drop( dropList, axis = 1 )
        

        # fill missing data first with previous days value
        # up to maximum of maxFill

        df.fillna( method = 'pad', limit = kwargs[ 'maxFill' ], inplace = True )
        df.fillna( df.mean(), inplace = True ) # fill remainder with station avg

        self.hydro = df.dropna( axis = 1 ) # drop stations with all nan

        print 'done hydro data'

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

        # perform feature scaling
        weatherScaler = preprocessing.StandardScaler().fit( xTrain )
        xTrain = weatherScaler.transform( xTrain )
        self.weatherScaler = weatherScaler

        if kwargs[ 'simpleModel' ]:
            model = RidgeCV( alphas = np.logspace( -2., 2. ) )
        else:
            model = ExtraTreesRegressor( n_estimators = 50, n_jobs = 4,
                                         random_state = 42 )
            
        model.fit( xTrain, yTrain )

        self.flowModel = model

    def fitLakeLevels( self, flowData, lakeData, **kwargs ):
        # model lake levels from stream flows
        
        xTrain = self.setDelay( flowData, kwargs[ 'nDays' ] )

        flowScaler = preprocessing.StandardScaler().fit( xTrain )
        xTrain = flowScaler.transform( xTrain )
        self.flowScaler = flowScaler

        # fit to daily changes in elevation
        yTrain = lakeData - np.roll( lakeData, 1 )
        yTrain[ 0 ] = 0.


        if kwargs[ 'simpleModel' ]:
            model = RidgeCV( alphas = np.logspace( -2., 2. ) )
        else:
            model = ExtraTreesRegressor( n_estimators = 50, n_jobs = 4,
                                         random_state = 42 )
        

        model.fit( xTrain, yTrain )

        self.lakeModel = model

        ypreds = model.predict( xTrain )
        lakePreds = lakeData[ 0 ] + np.cumsum( ypreds )

        plt.clf()
        plt.plot( self.dates, yTrain + lakeData, label = 'Actual' )
        plt.plot( self.dates, lakePreds, label = 'Predicted' )

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
        # use this method to predict future lake levels from rainfall data.
        # Calls modelHistorical() to first train the model
        
        self.modelHistorical( **kwargs )

        self.testDates = pd.date_range( kwargs[ 'testStartDate' ],
                                        kwargs[ 'testEndDate' ] )

        self.readWeather( self.testDates, test = True, **kwargs )
        self.flood( **kwargs ) # make up a simulated flood
        
        # use fitted model to predict new flows and lake levels

        lakeLevels1 = self.predictForward( fudge = False, **kwargs )
        lakeLevels2 = self.predictForward( fudge = True, **kwargs )

        dates = self.testDates
        lakeActual = self.lake.loc[ dates ].values

        plt.clf()
        
        plt.plot( dates, lakeActual, 'b', label = 'Historical' )
        plt.plot( dates, lakeLevels1, 'r', label = 'Simulated Flood' )
        plt.plot( dates, lakeLevels2, 'g', label = 'Simulated Flood (Fudged)' )
        plt.ylabel( 'Lake Travis Elevation (ft)' )
        plt.xlabel( 'Date' )
        plt.legend( loc = 2 )

        fig = plt.gcf()
        fig.autofmt_xdate()
        
        
        plt.savefig( 'flood.png' )
        


    def gaussian( self, xx, height, sigma ):

        # 2D gaussian centered on lake travis
        
        f = height * np.exp( -1. * ( xx**2 / ( 2. * sigma )**2 ) )
        return f


    def latlonToMiles( self, loc1, loc2 ):
        
        # loc is [ lat, lon ]
        
        dLon = np.radians( loc1[ 1 ] - loc2[ 1 ] )
        dLat = np.radians( loc1[ 0 ] - loc2[ 0 ] )

        a = ( np.sin( dLat / 2. ) )**2 + np.cos( np.radians( loc1[ 0 ] ) ) * np.cos( np.radians( loc2[ 0 ] ) ) * ( np.sin( dLon / 2. ) )**2
        
        c = 2. * np.arctan2( np.sqrt( a ), np.sqrt( 1 - a ) )
        miles = 3961. * c # 3961 is radius of Earth in miles

        return miles

    def flood( self, **kwargs ):

        # define a function to distribute rainfall based on distance from
        # center of the storm.  Using a gaussian for now..

        center = [ 30.438758,-97.931812 ] # lake travis
        #center = [ 30.816167,-98.412888 ] # lake buchannan
        
        dispersion = 100. # miles

        # FWHM = 2.35 * dispersion
        height = 3048. # tenths of mm ( = 1 foot ) max rainfall

        #height *= 5.

        # then call latlonToMiles on each station to determine
        # that station's distance from the epicenter

        weather = self.testWeather
        dates = pd.date_range( start = kwargs[ 'floodStartDate' ],
                               end = kwargs[ 'floodEndDate' ] )

        keys = self.weather.columns
        stations = self.weatherLocs        
        for date in dates:
            for key in keys:
                dist = self.latlonToMiles( center, stations[ key ] )
                rain = self.gaussian( dist, height, dispersion )
                weather.loc[ date, key ] = rain

        # write out grid of lat/lon vs rainfall for plotting in R
        latSpacing = np.linspace( center[ 0 ] - 8., center[ 0 ] + 8, num = 200 )
        lonSpacing = np.linspace( center[ 1 ] - 8., center[ 1 ] + 8, num = 200 )

        grid = np.meshgrid( latSpacing, lonSpacing )
        latlonGrid = zip( *[ x.flat for x in grid ] )

        dists = []
        for coord in latlonGrid:
            dists.append( self.latlonToMiles( center, coord ) )

        # couldn't get it to vectorize properly, so I gave up

        #getDists = np.vectorize( self.latlonToMiles )
        #dists = getDists( center, latlonGrid )

        #getRain = np.vectorize( self.gaussian )
        #rain = getRain( dists, height, dispersion )

        rain = []
        for dist in dists:
            rain.append( self.gaussian( dist, height, dispersion ) )

        fp = open( 'rainfall.out', 'w' )
        for i, j in zip( latlonGrid, rain ):
            inches = j / 3048. * 12
            out = str( i[ 0 ] ) + ',' + str( i[ 1 ] ) + ',' + str( inches ) + '\n'
            fp.write( out )

        fp.close()
        
        self.testWeather = weather

    def interpolateTestWeather( self, **kwargs ):
        # don't call this method any more

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

        df.iloc[ -20:-15, : ] = 1000.

        self.testWeather = df # overwrite previous with interpolated

    def predictForward( self, fudge = False, **kwargs ):

        # have stream flows predict delta lake height.  Track
        # lake levels from these deltas

        print 'predicting new lake levels from flood'

        nDays = kwargs[ 'nDays' ]
        xTest1 = self.setDelay( self.testWeather.values, nDays )
        xTest1 = self.weatherScaler.transform( xTest1 )

        floodDate = 23 # HARD CODED!!!

        flows = self.predFlowRates( xTest1 )
        if fudge:
            stations = self.hydro.columns
            fudgeFile = open( kwargs[ 'fudgeFile' ] )
            for line in fudgeFile:
                station = int( line.split()[ 0 ] )
                flow = float( line.split()[ 1 ] )
                dim = np.where( stations == station )[ 0 ][ 0 ]
                flows[ floodDate, dim ] = flow

            fudgeFile.close()
            
        
        xTest2 = self.setDelay( flows, nDays )
        xTest2 = self.flowScaler.transform( xTest2 )
        lakeChanges = self.predLakeLevels( xTest2 )

        lakeStart = self.lake.loc[ self.testDates[ 0 ] ].values
        lakePreds = lakeStart + np.cumsum( lakeChanges )

        return lakePreds


    def predFlowRates( self, inpWeather ):

        model = self.flowModel
        return model.predict( inpWeather )

    def predLakeLevels( self, inpFlows ):
        model = self.lakeModel
        return model.predict( inpFlows )



def main( **kwargs ):


    colorado = Basin( **kwargs )
    colorado.predict( **kwargs )
    #colorado.modelHistorical( **kwargs )
    #colorado.findImportantStations( colorado.lakeModel, 10, **kwargs )


    import pdb; pdb.set_trace()

    
    
    

if __name__ == '__main__':
    kwargs = { 'lakeFile': '/Users/jardel/blog/drought/travis_levels.dat',
               'weatherFile': '/Users/jardel/blog/drought/noaa.weather.big',
               'hydroFile': '/Users/jardel/blog/drought/usgs.dailyaverages/output',
               'stationFile': '/Users/jardel/blog/drought/stations.list',
               'stationNamesFile': '/Users/jardel/blog/drought/stations.latlon',
               'startDate': '2007-10-01',
               'endDate': '2012-12-31',
               'nDays': 0,
               'maxFill': 5,
               'completenessThreshold': .5,
               'simpleModel': True,
               'testWeatherFile': '/Users/jardel/blog/drought/noaa.weather.raw',
               'testStartDate': '2012-12-01',
               'testEndDate': '2012-12-31',
               'floodStartDate': '2012-12-24',
               'floodEndDate': '2012-12-24',
               'fudgeFile': '/Users/jardel/blog/drought/historical_flows.dat'
               }
    main( **kwargs )
