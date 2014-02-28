# takes smallSet2.tab (a small slice of the data) and returns
# another table with a column indicating if a coupon was used.
# Since Labor_Time doesn't always have entries, this does a beter job at
# filling in those blanks when calculating total labor time per RO.



# first pass to populate laborTimesDict
laborTimesDict = {}
with open( 'smallSet2.tab' ) as fp:
    fp.readline()
    for line in fp:
        arr = line.split( '\t' )
        dealer = arr[ 0 ]
        laborTime = arr[ 18 ].split( '^' )
        opCodes = arr[ 17 ].split( '^' )

        for op in zip( opCodes,laborTime ):
            if op[ 1 ]: # laborTime is not null
                if laborTimesDict.has_key( dealer ):
                    if laborTimesDict[ dealer ].has_key( op[ 0 ] ):
                        # compute mean including this new labor time value
                        tmp = laborTimesDict[ dealer ][ op[ 0 ] ]
                        new = ( tmp[ 0 ] * tmp[ 1 ] + float( op[ 1 ] ) ) \
                            / ( tmp[ 1 ] + 1 )
                        laborTimesDict[ dealer ][ op[ 0 ] ] = [ new, tmp[ 1 ] + 1 ]
                    else:
                        # add op for this dealer for the first time
                        laborTimesDict[ dealer ][ op[ 0 ] ] = [ float( op[ 1 ] ), 1 ]
                else:
                    #this dealer isn't in laborTimesDict yet
                    laborTimesDict[ dealer ] = { op[ 0 ]: [ float( op[ 1 ] ), 1 ] }
                    
                    
# laborTimesDict is now a dictionary holding the average labor time for a
# given OP code at each dealership.  We can use this to look up missing values

fw = open( 'FsmallSet2.tab', 'w' ) # F for filled
with open( 'smallSet2.tab' ) as fp:
    fp.readline()
    for line in fp:
        arr = line.split( '\t' )
        dealer = arr[ 0 ]
        laborTime = arr[ 18 ].split( '^' )
        opCodes = arr[ 17 ].split( '^' )

        s = 0
        for op in zip( opCodes, laborTime ):
            if op[ 1 ]: # laborTime not null
                s += float( op[ 1 ] )
            else:
                # look up in laborTimeDict
                if laborTimesDict[ dealer ].has_key( op[ 0 ] ):
                    s += laborTimesDict[ dealer ][ op[ 0 ] ][ 0 ]
                

        totalLabor = s

        # check to see if this RO used a coupon
        desc1 = arr[ -1 ]
        desc2 = arr[ -2 ]
        if 'COUPON' in desc1.upper() or 'COUPON' in desc2.upper():
            isCoupon = 'y'
        else:
            isCoupon = 'n'

        # re-expand array back into string
        out = ''
        for item in arr[ :-2 ]:
            out += item + '\t'
        out += str( totalLabor ) + '\t' + isCoupon + '\n'
        fw.write( out )
        if len( arr ) > 50:
            print arr

fw.close()        
                


