import csv
import sys

# take the horriblly messy file containing election results by district and
# candidate and turn it into a nice pretty csv file to be read in.

def two_party( returns ):
    # pick out the top 2 candidates receiving votes.  Should be Republican
    # and Democrat in almost every race.
    # Output margin of victory.
    returns.sort( key = lambda percentage: percentage[ 1 ], reverse = True )
    top2 = returns[ :2 ]
    R = 1
    D = 1
    for party in top2:
        if 'R' in party:
            repub = str( party[ 1 ] )
            R -= 1
        elif 'D' in party:
            dem = str( party[ 1 ] )
            D -= 1
    if R != 0 or D != 0:
        # if a third party wins more votes, output zero margin of victory
        repub = '0'
        dem = '0'
    sParty = repub + ',' + dem
    return sParty


outfile = open( 'election_results.csv', 'w' )
fp = open( 'election_res_prelim.csv' )
reader = csv.reader( fp )
reader.next()

returns = []
workingDistrict = '01'
iLoop = 1
for row in reader:
    if row[ 2 ] == workingDistrict:
        returns.append( [ row[ 3 ], float( row[ 4 ] ) ] )
    elif row[ 2 ] == '':
        continue
    else:
        # do the analysis when working district changes
        results = two_party( returns )
        if results == '0,0':
            print row[ 1 ] + '-' + workingDistrict + ' not a 2-party race'
        out = row[ 1 ] + '-' + workingDistrict + ',' + results + '\n'
        outfile.write( out )
        if iLoop == 2:
            pass
        returns = [] # re-initialize returns when the calculation is done
        returns.append( [ row[ 3 ], float( row[ 4 ] ) ] )
        workingDistrict = row[ 2 ]
        iLoop += 1


# Looks ok now
