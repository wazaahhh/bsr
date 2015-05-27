import numpy as np
import pylab as pl

import boto
import zlib
import json
import re
from pspectrumlib import *



fig_width_pt = 420.0  # Get this from LaTeX using \showthe\columnwidth
inches_per_pt = 1.0 / 72.27  # Convert pt to inch
golden_mean = (np.sqrt(5) - 1.0) / 2.0  # Aesthetic ratio
fig_width = fig_width_pt * inches_per_pt  # width in inches
fig_height = fig_width  # *golden_mean      # height in inches
fig_size = [fig_width, fig_height]

params = {'backend': 'ps',
          'axes.labelsize': 25,
          'text.fontsize': 32,
          'legend.fontsize': 18,
          'xtick.labelsize': 20,
          'ytick.labelsize': 20,
          'text.usetex': False,
          'figure.figsize': fig_size}
pl.rcParams.update(params)


bucketName = "brainspeedr"
s3 = boto.connect_s3()
global bucket
bucket = s3.get_bucket(bucketName)

global subjects
subjects = ["8db55","92647","ac3ef","f62ff","29979","d6dbd","2cd39","85d6e","5f615","94460"]

def retrieveExperiment(token):
    list = bucket.list("bsr/v1.0/%s"%token)
    expJson = {}
    listDic = {}
    for i,l in enumerate(list):
        #print re.findall("%s/(.*?)\."%token,l.name)[0]
        id = re.findall("%s/(.*?)\."%token,l.name)[0]
        listDic[i] = id
        expJson[id] = json.loads(zlib.decompress(l.get_contents_as_string()))
    return expJson,listDic



def plotRateEntropy(json):
    time = json['exp']['timestamps']
    rate = json['exp']['rate']
    entropy = json['exp']['normalized_entropy']
    
    pl.figure(1,(8,18))
    pl.subplot(211)
    pl.plot(time,rate)
    pl.subplot(212)
    pl.plot(time,entropy)   
    
    
def plotTimeSeries(dictionary,treatment,valueType="rate"):
    dic = dictionary[treatment]['exp']
    time = dic['timestamps']
    values = dic[valueType]
    #print len(time),len(values)
    pl.plot(time,values,'.')
    pl.xlabel("Time [word index]")
    pl.ylabel(valueType)
    
    if valueType in ['entropy','normalized_entropy']:
        smoothing = 10
        valuesConv = np.convolve(values,np.zeros([smoothing])+1./smoothing)[:-smoothing+1]
        plot(time,valuesConv,'r-',lw=1)

    