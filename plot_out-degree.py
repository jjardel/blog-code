import matplotlib.pyplot as plt
import numpy as np
from scipy import optimize

def fitfunc( x, a, b ):
    func = a * x + b
    return func

def fitexp( x, a, b, c ):
    func = b * np.exp(  a * x ) + 0.
    return func

# read in ans.tex 
# format is: out-degree, number of subjects with that out-degree

h = {}
f = open( 'ans.txt' )
for line in f:
    degree = int( line.split()[ 0 ] )
    N = int( line.split()[ 1 ] ) 
    if h.has_key( degree ):
        h[ degree ] = h[ degree ] + N
    else:
        h[ degree ] = N
f.close()

x = np.array( h.keys() )
y = np.array( h.values() )

# fit a line and get slope
log_x = np.log10( x[ x < 1e4 ] )
log_y = np.log10( y[ x < 1e4 ] ) 
p0 = [ -5, 5. ]

pfit, cov = optimize.curve_fit( fitfunc, log_x, log_y, p0 = p0 )
x_fit = np.logspace( 0, 7 )
y_fit = 10**( pfit[ 1 ] + pfit[ 0 ] * np.log10( x_fit ) )

# fit an exp
p0 = np.array( [ -5, 20, 0. ] )
pfit2, cov2 = optimize.curve_fit( fitexp, np.array( x ), np.array( y ),
                                  p0 = p0 )
print pfit
print pfit2

exp_fit = np.vectorize( fitexp )
y_exp = exp_fit( x_fit, pfit2[ 0 ], pfit2[ 1 ], pfit2[ 2 ] )
plt.clf()

plt.loglog( x, y, 'ko' )
plt.loglog( x_fit, y_fit, 'r', linewidth = '2', 
            label = '$N \\propto \\mathrm{degree}^{-2.2}$' )
plt.loglog( x_fit, y_exp, 'b', linewidth = '2', 
            label = '$N \\propto e^{-\\mathrm{degree}}$' )
plt.ylim( [ 1, 1e8 ] )

ax = plt.gca()
#plt.text( 0.2, 0.8, '$\\propto \mathrm{degree}^{-2.2}$',
#          transform = ax.transAxes, fontsize = '16' )
plt.xlabel( 'out-degree' )
plt.ylabel( 'N' )
plt.legend()
            

plt.savefig( 'out-degree.png' )
plt.show()
