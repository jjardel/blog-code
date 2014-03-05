"""
Make an 'everything-vs-everything' plot of all the features in my ranking metric.
Initially used to diagnose and eliminate features that were strongly dependent
so as to avoid double counting in the metric.

I later found a (possibly) interesting correlation between out of warranty sales
and efficiency.
"""


import numpy as np
import matplotlib.pyplot as plt
import csv
from sklearn.preprocessing import MinMaxScaler
from scipy.stats import spearmanr
from scipy.stats import pearsonr
from scipy.stats import linregress

with open( 'metric1.out' ) as fp:
    reader = csv.reader( fp )
    metric = []
    dealerIDs = []
    for row in reader:
        metric.append( row[ 1: ] )
        dealerIDs.append( int( row[ 0 ] ) )

metric = np.array( metric, dtype = 'float' )
scaler = MinMaxScaler()
X = scaler.fit_transform( metric )

plt.clf()
nFeatures = metric.shape[ 1 ]
fig, axs = plt.subplots( nFeatures, nFeatures )

iName = 0
names = [ 'SALES', 'EFFICIENCY', 'OUT\nOF\nWARRANTY',
          'LOYALTY', 'GROWTH' ]

# Setup the grid of correlation plots

for i in range( nFeatures ):
    for j in range( nFeatures ):
        if i < j: # avoid plotting same thing twice
            axs[ i, j ].plot( X[ :, i ], X[ :, j ], 'k.' )
            if j != ( i + 1 ):
                # only put labels on the bottom panels
                axs[ i, j ].set_xticklabels( [] )
                axs[ i, j ].set_yticklabels( [] )
            else:
                # set the labels manually for no overlap
                axs[ i, j ].set_xticklabels( [ '0.', '', '0.4', '', '0.8' ] )
                axs[ i, j ].set_yticklabels( [ '0.', '', '0.4', '', '0.8' ] )                                        
        elif i == j:
            # put titles on diagonal squares
            axs[ i, j ].text( 0., 0.2, names[ iName ],
                              transform = axs[ i, j ].transAxes,
                              fontsize = '9' )
            axs[ i, j ].axis( 'off' )
            iName += 1
        else:
            axs[ i, j ].axis( 'off' )

# checking correlation between efficiency and loyalty
warranty = X[ :, 2 ]
efficiency = X[ :, 1 ]

y = efficiency[ warranty > 0.1 ]
x = warranty[ warranty > 0.1 ]

slope, intercept, r_value, p_value, std_err = linregress( x, y )
print 'PEARSON R, R**2 VALUE'
print r_value, r_value**2

xfit = np.linspace( 0., 1., num = 50 )
yfit = slope * xfit + intercept
axs[ 1, 2 ].plot( xfit, yfit, 'r' )

plt.savefig( 'everything.png' )
