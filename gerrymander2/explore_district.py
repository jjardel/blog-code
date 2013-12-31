import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from sklearn.cluster import KMeans
from sklearn.svm import OneClassSVM
from sklearn import preprocessing
import csv
import sys

from animate import *

# make 3d scatterplot of district features

n = 0
with open( 'districts.csv' ) as fp:
    reader = csv.reader( fp )
    for row in reader:
        n += 1

data = np.zeros( ( n, 3 ) )
names = []
parties = []
i = 0
with open( 'districts.csv' ) as fp:
    reader = csv.reader( fp )
    for row in reader:
        data[ i, 0 ] = row[ 1 ]
        data[ i, 1 ] = row[ 3 ]
        data[ i, 2 ] = row[ 4 ]
        names.append( row[ 0 ] )
        parties.append( row[ 2 ] )
        i += 1
data[ :, 1 ] = abs( data[ :, 1 ] )

parties = np.array( parties )
repubs = np.where( parties == 'Republican' )[ 0 ]
dems = np.where( parties == 'Democrat' )[ 0 ]

R = data[ repubs, : ]
D = data[ dems, : ]

plt.clf()

fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')
#ax.scatter( data[ :, 0 ], data[ :, 1 ], data[ :, 2 ] )
ax.scatter( R[ :, 0 ], R[ :, 1 ], R[ :, 2 ], c = 'r' )
ax.scatter( D[ :, 0 ], D[ :, 1 ], D[ :, 2 ], c = 'b' )
ax.set_xlabel( 'Ratio' )
ax.set_ylabel( 'Margin' )
ax.set_zlabel( 'Similarity of Neighboring Districts' )
ax.set_zlim( [ 0., 1. ] )
ax.set_xlim( [ 0., 500. ] )
ax.set_ylim( [ 0., 1. ] )

fig.show()

angles = np.linspace(0,360,41)[:-1] # Take 20 angles between 0 and 360
rotanimate(ax, angles,'movie.gif',delay=20, width = 6., height = 5.) 

# do outlier search using one-class SVM
data[ 0, : ] = preprocessing.scale( data[ 0, : ] )

model = OneClassSVM( gamma = .001, nu = .1 )
fit = model.fit( data )
preds = model.predict( data )

inlier = np.where( preds == 1. )[ 0 ]
outlier = np.where( preds == -1. )[ 0 ]

fig = plt.figure()
ax = fig.add_subplot( 111, projection = '3d' )
ax.scatter( data[ inlier, 0 ], data[ inlier, 1 ], data[ inlier, 2 ], c = 'b' )
ax.scatter( data[ outlier, 0 ], data[ outlier, 1 ], data[ outlier, 2 ], c = 'k' )
ax.set_xlabel( '$P^2/A$' )
ax.set_ylabel( 'Margin' )
ax.set_zlabel( 'Similarity of Neighboring Districts' )

ax.set_ylim( [0., 1 ] )
ax.set_zlim( [ 0., 1. ] )


fig.show()
"""


n_clusters = 2
model = KMeans( n_clusters = n_clusters, init = 'random' )

# feature scaling
data = preprocessing.scale( data )

model.fit( data )
preds = model.predict( data )


fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')
icolor = [ 'r', 'b', 'g', 'k' ]
for nc in range( n_clusters ):
    clust = np.where( preds == nc )[ 0 ]
    ax.scatter( data[ clust, 0 ], data[ clust, 1 ],
                data[ clust, 2 ], c = icolor[ nc ] )

ax.set_xlabel( '$P^2/A$' )
ax.set_ylabel( 'Margin' )
ax.set_zlabel( 'Fraction of Neighboring Districts Under Same Party Control' )

fig.show()

"""
