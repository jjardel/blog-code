import shapefile as sf
import numpy as np
import shapely.geometry
import matplotlib.pyplot as plt
from pyproj import Proj
import csv


class District( sf._Shape ):
    def __init__( self, shape, record ):
        self.ratio = 0
        self.coords = np.array( shape.points )
        self.state = ''
        self.name = ''

        # get shape and record data
        self.shape = shape
        self.get_record( record )

    def get_record( self, record ):
        self.state = fips[ record[ 0 ] ]
        self.name = self.state + '-' + record[ 1 ]
 
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
        ratio = perimeter / area
    
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

# write out coordinates of districts with 10 largest ratios for ploting
top10Inds = inds[ :10 ]
[ district.write_coords() for district in districts[ top10Inds ] ]

# write out sorted list of ratios
with open( 'ratios.out', 'w' ) as f:
    for i, j in zip( names[ inds ], ratios[ inds ] ):
        out = i + '\t' + str( j ) + '\n'
        f.write( out )

# get array with party affiliations for each district
parties = []        
for district in districts:
    try:
        parties.append( party[ district.name ] ) # some of these aren't
                                                 # defined for some reason
    except:
        parties.append( 'N/A' )
        print district.name


parties = np.array( parties )        
nParties = np.zeros( n )
democrats = np.where( parties == 'Democrat' )
republicans = np.where( parties == 'Republican' )
na = np.where( parties == 'N/A' )

D = ratios[ democrats ]
R = ratios[ republicans ]

plt.hist( ( D, R ), bins = 50, log = False, histtype = 'barstacked',
          color = ( 'b', 'r' ), label = ( 'Democrat', 'Republican' ) )
plt.legend()
plt.xlabel( 'Perimeter / Area' )
plt.ylabel( 'N' )
#plt.show()
plt.savefig( 'histrogram.png' )
