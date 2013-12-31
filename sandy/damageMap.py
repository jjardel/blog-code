import csv
import re
from bs4 import BeautifulSoup
import matplotlib.pyplot as plt
import numpy as np
import shapefile as sf


def cleanNumeric( inp ):
    # scrub the excel spreadsheet of $s and ,s
    noDollar = re.sub( '\$', '', inp )
    noComma = re.sub( ',', '', noDollar )
    return noComma


class ReadMyCSV:
    def __init__( self, filename ):
        self.filename = filename
        self.claimsDict = self.read()
                
    def read( self ):
        with open( self.filename, 'rU' ) as fp:
            dialect = csv.Sniffer().sniff( fp.read( 1024 ) )
            fp.seek( 0 )
            reader = csv.reader( fp, dialect )
            zips = []
            medianIncome = []
            nClaims = []
            damage = []
            reader.next()
            
            claimsDict = {}
            # create a dictionary of the claims with zip code as the key and 
            # [ damage, medianIncome, nClaims ] as the value
            for row in reader:
                if 'NJ' in row[ 0 ]:
                    zipCode = int( row[ 3 ] )
                    medianIncome = float( cleanNumeric( row[ 6 ] ) )
                    claim = int( cleanNumeric( row[ 4 ] ) )
                    damage = float( cleanNumeric( row[ 14 ] ) )
                    aid = float( cleanNumeric( row[ 21 ] ) )
                    
                    if zipCode in claimsDict.keys():
                        claimsDict[ zipCode ][ 0 ] += damage
                        claimsDict[ zipCode ][ 1 ] = np.mean(
                            [ claimsDict[ zipCode ][ 1 ], medianIncome ] )
                        claimsDict[ zipCode ][ 2 ] += claim
                        claimsDict[ zipCode ][ 3 ] += aid
                    else:
                        claimsDict[ zipCode ] = [ damage, medianIncome,
                                                  claim, aid  ]
                        
                    
            return claimsDict
                

def readContractsFile( filename ):
    # read contracts file, sum the total award by city then return a
    # dictionary holding the zip codes as keys and total award as values

    # convert city names to zips
    zipFile = 'zip-lookup.csv'
    zipDict = loadZipTable( zipFile )

    contracts = {}

    with open( filename, 'rU' ) as fp:
        reader = csv.reader( fp )
        reader.next()
        for row in reader:
            value = float( cleanNumeric( row[ 2 ][ 1: ] ) )
            city = row[ 5 ]
            if city in contracts.keys():
                contracts[ city ] += value
            else:
                contracts[ city ] = value

    contractsByZip = {}
    for city in contracts.keys():
        try:
            zips = zipDict[ city ]
            n = len( zips )
            for zipCode in zips:
                # spread a city's contracts over all its zip codes
                contractsByZip[ zipCode ] = contracts[ city ] / n
        except:
            pass
            
    return contractsByZip


def loadZipTable( zipFile ):
    # have a zipcode lookup table reverse-indexed as key: city, value: zipcodes
    zipDict = {}
    with open( zipFile, 'rU' ) as fp:
        reader = csv.reader( fp )
        reader.next()
        for row in reader:
            zipCode = row[ 0 ]
            city = row[ 1 ].upper()
            if city in zipDict.keys():
                zipDict[ city ].append( zipCode )
            else:
                zipDict[ city ] = []
                zipDict[ city ].append( zipCode )
    return zipDict
            

def getBaseMap():
    # for making .svg maps of the zip codes --not the best way
    svg = open( 'nj_zips.svg' ).read()
    soup = BeautifulSoup( svg, 'xml' )
    return soup


def plotQuantity( soup, mapping ):
    # make the map
    # mapping is dict containing mapping[ zip ] = color 

    baseStyle = 'fill:'
    paths = soup.find_all( 'path' )
    
    for p in paths:
        if p[ 'data-zcta5ce10' ] in mapping.keys():
            p[ 'style' ] = baseStyle + mapping[ p[ 'data-zcta5ce10' ] ]

    #import pdb; pdb.set_trace
    return soup

def setLayerMap( zips, f, nColors, logScale = True ):
    # get the scale right for the fill colors
    mapping = {}
    levels = [ '#FFFFFF', '#FFFFB2', '#FECC5C', '#FD8D3C', '#F03B20', '#BD0026' ]
    
    # if using a log scale, awkwardly avoid zeros
    if logScale:
        notZero = np.where( f != 0 )[ 0 ]
        isZero = np.where( f == 0 )[ 0 ]
        lf = np.zeros( len( f ) )
        lf[ notZero ] = np.log10( f[ notZero ] )
        lf[ isZero ] = 0
        f = np.copy( lf )

    # automatically set the scaling relative to the median
    # there's got to be a better way to do this, but at least it's robust to outliers
    median = np.median( f )
    deltaF = 2 * median / nColors

    indices = np.floor( f / deltaF )
    tooBig = np.where( indices >= nColors )[ 0 ]
    indices[ tooBig ] = nColors - 1
        
    mapping = {}
    for z, i in zip( zips, indices ):
        try:
            mapping[ str( z ).rjust( 5, '0' ) ] = levels[ int( i ) ]
        except ValueError:
            mapping[ str( z ).rjust( 5, '0' ) ] = levels[ 0 ]

    #import pdb; pdb.set_trace()

    return mapping

def calcDiff( damageDict, contractsDict ):
    # calculate difference between damage and contracts awarded
    difference = []
    zips = []
    for key in damageDict:
        if key in contractsDict.keys():
            difference.append( damageDict[ key ] - contractsDict[ key ] )
        else:
            difference.append( damageDict[ key ] )
        zips.append( int( key ) )

    return zips, difference

def writeCSVdata( mapping, claimsDict,filename ):
    # write out CSV file mapping the zip code to fill color for later plotting
    # with R
    
    fw = open( filename, 'w' )
    writer = csv.writer( fw )
    writer.writerow( [ "zip", "color" ] )
    for key in claimsDict.keys():
        if str( key ).rjust( 5, '0' ) in mapping.keys():
            m = mapping[ str( key ).rjust( 5, '0' ) ]
        else:
            m = "#FFFFFF"
            
        writer.writerow( [ str( key ).rjust( 5, '0' ), m ] )
    fw.close()


if __name__ == '__main__':
    # read in zip code, total damage $,
    fOwners = 'damage-owners.csv'
    fRenters = 'damage-renters.csv'

    claimsDict = ReadMyCSV( fOwners ).claimsDict
    
    income = np.array( [ claims[ 1 ] for claims in claimsDict.values() ] )
    damage = np.array( [ claims[ 0 ] for claims in claimsDict.values() ] )
    zips = np.array( claimsDict.keys() )

    # damage mapping
    base = getBaseMap()
    damageMapping = setLayerMap( zips, damage, 5 )
    damageLayer = plotQuantity( base, damageMapping )
    writeCSVdata( damageMapping, claimsDict, 'damage.csv' )
    
    mapFile = open( 'damage.svg', 'w' )
    mapFile.write( damageLayer.prettify() )
    mapFile.close()

    damageDict = {}
    for k, v in zip( zips, damage ):
        damageDict[ str( k ) ] = v

    # difference in all contracts map
    contracts = readContractsFile( 'contracts.csv' )
    zips2, difference = calcDiff( damageDict, contracts )
    zips2 = np.array( zips2 )
    difference = np.array( difference )

    good = np.where( difference > 0 )[ 0 ]
    diffMapping = setLayerMap( zips2[ good ], difference[ good ], 5 )
    writeCSVdata( diffMapping, claimsDict, 'diff.csv' )

    # income map
    incomeMapping = setLayerMap( zips, income, 5, logScale = False )
    writeCSVdata( incomeMapping, claimsDict, 'income.csv' )

    # difference in aid map
    aidDiff = []
    for z in zips:
        aidDiff.append( ( claimsDict[ z ][ 0 ] - claimsDict[ z ][ 3 ] ) )
                        
    aidDiff = np.array( aidDiff )
    good = np.where( aidDiff > 0 )[ 0 ]
    aidMapping = setLayerMap( zips[ good ], aidDiff[ good ], 5 )
    writeCSVdata( aidMapping, claimsDict, 'aidDiff.csv' )

    # income scaled map
    scaled = []
    for z in zips:
        try:
            scaled.append( ( claimsDict[ z ][ 0 ] - claimsDict[ z ][ 3 ] ) /
                           claimsDict[ z ][ 1 ] * 1000 )
        except:
            scaled.append( 0. )
        
    scaled = np.array( scaled )
    good = np.where( scaled > 0 )[ 0 ]
    scaledMapping = setLayerMap( zips[ good ], scaled[ good ], 5 )
    writeCSVdata( scaledMapping, claimsDict, 'scaled.csv' )
    
                    
