import shapefile as sf

def main( **kwargs ):

    stationList = []
    with open( kwargs[ 'stationlist' ] ) as stationFile:
        for line in stationFile:
            stationList.append( line.rstrip() )

    ID = []
    lat = []
    lon = []
    name = []
    f = sf.Reader( kwargs[ 'shapefile' ] )
    records = f.records()
    for record in records:
        if record[ 0 ] in stationList:
            ID.append( record[ 0 ] )
            name.append( record[ 24 ].replace( ',', ' ' ) )
            lat.append( float( record[ 6 ] ) )
            lon.append( float( record[ 5 ] ) )

    fw = open( 'stations.latlon', 'w' )
    for item in zip( ID, name, lat, lon ):
        out = '%(id)s, %(name)s, %(lat)s, %(lon)s \n' % { 'id': item[ 0 ],
                                                          'name': item[ 1 ],
                                                          'lat': item[ 2 ],
                                                          'lon': item[ 3 ]
                                                          }
        fw.write( out )



if __name__ == '__main__':
    kwargs = { 'shapefile': '/Users/jardel/blog/drought/qsitesdd_shp/qsitesdd',
               'stationlist': '/Users/jardel/blog/drought/stations.list'
               }
    main( **kwargs )

    
    
