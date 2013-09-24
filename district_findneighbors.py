import shapefile as sf
import numpy as np
import shapely.geometry
import matplotlib.pyplot as plt
from pyproj import Proj
import csv
import sys

# Process Congressional Districts and write out ratio, margin of victory for
# 2012 election, and the fraction of neighboring districts under the same party's
# control.  

"""
NOT A GOOD WAY TO DO THIS!
def is_neighbor( base, district, tol = 1e-10 ):
    baseCoords = base.coords
    districtCoords = district.coords
    isNeighbor = False
    for i in baseCoords:
        for j in districtCoords:
            dist = np.sqrt( ( i[ 0 ] - j[ 0 ] )**2 + ( i[ 1 ] - j[ 1 ] )**2 )
            if dist < tol:
                print dist
                return True
    return isNeighbor
"""

def is_neighbor( base, district ):
    # Use sets!  If two districts are neighbors, they will share at least
    # one coordinate for their border.
    joint = base.coords_set & district.coords_set
    if joint:
        return True
    else:
        return False

def find_neighbors( base_district, districts ):
    neighbors = []
    for district in districts:
        if is_neighbor( base_district, district ):
            # only take districts from the same state, and don't let a district
            # be its own neighbor
            if base_district.name[ :4 ] in district.name and base_district != district:
                neighbors.append( district.name )
    return neighbors

class District( sf._Shape ):
    def __init__( self, shape, record ):
        self.ratio = 0
        self.coords = np.array( shape.points )
        self.coords_set = set(  map( tuple,
                                    np.round( self.coords, decimals = 5 ) ) ) 
        self.state = ''
        self.name = ''

        # get shape and record data
        self.shape = shape
        self.get_record( record )
        self.party = party[ self.name ]

    def get_record( self, record ):
        self.state = fips[ record[ 0 ] ]
        self.name = self.state + '-' + record[ 1 ]
        try:
            results = elections[ self.name ]
            self.margin = results[ 0 ] - results[ 1 ] # positive
                                                      # margin = republican
                                                      # victory
        except:
            self.margin = 0.
            print 'no results for ' + self.name
            
    def project( self ):
        # project the lat/lon coordinates into an equal-area projection

        # get box to center projection on
        bbox = self.shape.bbox
        lat_1 = str( bbox[ 1 ] )
        lat_2 = str( bbox[ 3 ] )
        lat_0 = str( np.mean( [ bbox[ 1 ], bbox[ 3 ] ] ) )
        lon_0 = str( np.mean( [ bbox[ 0 ], bbox[ 2 ]] ) )

        lat = self.coords[ :, 1 ]
        lon = self.coords[ :, 0 ]

        # do the projection
        pa = Proj( "+proj=aea +lat_1=" + lat_1 + " lat_2=" + lat_2 + " lat_0="
                   + lat_0 + " lon_0=" + lon_0 )
        x, y = pa( lon, lat )
        return x, y 

    def calc_ratio( self ):
        # calculate the ratio of a district's perimeter to its area to be
        # used as a feature to detect gerrymandering.
        
        x, y = self.project()
        dist_proj = {"type": "Polygon", "coordinates": [ zip( x, y ) ] }
        area = shapely.geometry.shape( dist_proj ).area
        perimeter = shapely.geometry.shape( dist_proj ).length
        ratio = perimeter**2 / area

        self.ratio = ratio
        return ratio

    def write_coords( self ):
        # write out the district's coordinates so I can make a pretty map in
        # R with ggmap.
        
        fp = 'R/' + self.name + '_coords.csv'
        np.savetxt( fp, self.coords, delimiter = ',', fmt = '%10.6f',
                    header = 'Longitude, Latitude', comments = '' )

        
        
# ====================================
# DICTIONARY HOLDING STATE FIPS CODES
fips = {}
with open( 'fips.csv' ) as fp:
    reader = csv.reader( fp )
    reader.next()
    for row in reader:
        fips[ row[ 0 ] ] = row[ 2 ]
# ====================================

# ====================================
# DICTIONARY HOLDING PARTY DATA
f = sf.Reader( 'cgd113p010g.shp' )
partyRecords = f.records()
party = {}
for record in partyRecords:
    key = record[ 0 ] + '-' + record[ 2 ]
    value = record[ 4 ]
    party[ key ] = value
# ====================================

# ====================================
# DICTIONARY HOLDING ELECTION RESULTS
elections = {}
with open( 'election_results.csv' ) as fp:
    reader = csv.reader( fp )
    for row in reader:
        elections[ row[ 0 ] ] = ( float( row[ 1 ] ), float( row[ 2 ] ) )
        if row[ 0 ] not in party.keys():
            if float( row[ 1 ] ) > float( row[ 2 ] ):
                party[ row[ 0 ] ] = 'Republican'
            else:
                party[ row[ 0 ] ] = 'Democrat'
# ====================================

f = sf.Reader( 'tl_2013_us_cd113.shp' )

fields = f.fields

shapes = f.shapes() # contains list of all shape instances
                    # shapes[ i ].points lists actual boundaries
 
records = f.records() # contains list of record information in same order
                      # as shapes

# Remove "at Large" districts
iRec = 0
for rec in records:
    if 'at Large' in rec[ 3 ]:
        bad = records.pop( iRec )
        bad = shapes.pop( iRec )
    iRec += 1

# Remove districts that have issues with islands
iRec = 0
for rec in records:
    if fips[ rec[ 0 ] ] == 'California' and rec[ 1 ] == '47':
        bad = records.pop( iRec )
        bad = shapes.pop( iRec )
    elif fips[ rec[ 0 ] ] == 'Hawaii' and rec[ 1 ] == '02':
        bad = records.pop( iRec )
        bad = shapes.pop( iRec )
    elif fips[ rec[ 0 ] ] == 'Michigan' and rec[ 1 ] == 'ZZ':
        bad = records.pop( iRec )
        bad = shapes.pop( iRec )
    elif fips[ rec[ 0 ] ] == 'Illinois' and rec[ 1 ] == 'ZZ':
        bad = records.pop( iRec )
        bad = shapes.pop( iRec )
    elif fips[ rec[ 0 ] ] == 'Guam' and rec[ 1 ] == '98':
        bad = records.pop( iRec )
        bad = shapes.pop( iRec )
    elif fips[ rec[ 0 ] ] == 'Connecticut' and rec[ 1 ] == 'ZZ':
        bad = records.pop( iRec )
        bad = shapes.pop( iRec )
    iRec += 1
 
n = len( records )

# calculate ratios

districts = []
ratios = []
for shape, record in zip( shapes, records ):
    d = District( shape, record )
    ratios.append( d.calc_ratio() )
    districts.append( d )
    
ratios = np.array( ratios )
names = [ district.name for district in districts ]

districts = np.array( districts )
names = np.array( names )
inds = np.argsort( -1. * ratios )

#sys.exit()

# find neighboring districts and party affils
for district in districts:
    neighbors = find_neighbors( district, districts )
    myParty = party[ district.name ]
    neighborParties = [ party[ neighbor ] for neighbor in neighbors ]
    nSame = float( neighborParties.count( myParty ) )
    nTotal = len( neighbors )
    try:
        fSame = nSame / nTotal
    except:
        fSame = 0.
    district.fSame = fSame

# write out the important stuff
f_res = open( 'districts.csv', 'w' )
for district in districts:
    out = district.name + ',' + str( district.ratio ) + ','
    out += district.party + ',' + str( district.margin ) + ','
    out += str( district.fSame ) + '\n'
    f_res.write( out )

f_res.close()
#sys.exit()

# write out coordinates of districts with 10 largest ratios for ploting
top10Inds = inds[ :10 ]
[ district.write_coords() for district in districts[ top10Inds ] ]

# write out sorted list of ratios
with open( 'ratios.out', 'w' ) as f:
    for i, j in zip( names[ inds ], ratios[ inds ] ):
        out = i + '\t' + str( j ) + '\n'
        f.write( out )

# get party afiils
parties = []
for district in districts:
    try:
        parties.append( party[ district.name ] ) # some of these aren't
                                                 # defined for some reason
    except:
        parties.append( 'N/A' )
        #print district.name


parties = np.array( parties )        
nParties = np.zeros( n )
democrats = np.where( parties == 'Democrat' )
republicans = np.where( parties == 'Republican' )
na = np.where( parties == 'N/A' )

D = ratios[ democrats ]
R = ratios[ republicans ]

plt.clf()

plt.hist( ( D, R ), bins = 50, log = False, histtype = 'barstacked',
          color = ( 'b', 'r' ), label = ( 'Democrat', 'Republican' ) )
plt.legend()
plt.xlabel( 'Perimeter$^2$ / Area' )
plt.ylabel( 'N' )
#plt.show()
plt.savefig( 'histrogram.png' )
