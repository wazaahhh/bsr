import numpy as np
import pylab as pl
from sklearn.decomposition import FastICA

A = np.sin(np.linspace(0,50, 1000))
B = np.sin(np.linspace(0,37, 1000)+5)
pl.figure(1,(12,8))
pl.subplot(211)
pl.plot(A)
pl.subplot(212)
pl.plot(B, 'r')


M1 = A - 2*B;                  
M2 = 1.73*A+3.41*B;            

pl.figure(2,(10,8))
pl.subplot(211); pl.plot(M1);
pl.subplot(212); pl.plot(M2, 'r');

pl.figure(3,(10,8))
ica = FastICA([M1,M2])
c = ica.fit([M1,M2])
pl.subplot(211); pl.plot(c(1,:));
pl.subplot(212); pl.plot(c(2,:));