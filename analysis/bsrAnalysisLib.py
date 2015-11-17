import sys
import numpy as np
import pylab as pl
from scipy import stats as S

import boto
import zlib
import json
import re

sys.path.append("/Users/maithoma/work/github/brainlib/")
from pspectrumlib import *

sys.path.append("/Users/maithoma/work/python/")
from tm_python_lib import *
import adaptive_kernel_tom as AK


fig_width_pt = 420.0  # Get this from LaTeX using \showthe\columnwidth
inches_per_pt = 1.0 / 72.27  # Convert pt to inch
golden_mean = (np.sqrt(5) - 1.0) / 2.0  # Aesthetic ratio
fig_width = fig_width_pt * inches_per_pt  # width in inches
fig_height = fig_width  # *golden_mean      # height in inches
fig_size = [fig_width, fig_height]

params = {'backend': 'ps',
          'axes.labelsize': 22,
          'text.fontsize': 32,
          'legend.fontsize': 18,
          'xtick.labelsize': 18,
          'ytick.labelsize': 18,
          'text.usetex': False,
          'figure.figsize': fig_size}
pl.rcParams.update(params)


bucketName = "brainspeedr"
s3 = boto.connect_s3()
global bucket
bucket = s3.get_bucket(bucketName)

global subjects
subjects = ["8db55","92647","ac3ef","f62ff","29979","d6dbd","2cd39","85d6e","5f615","94460"]

def compute_entropy(raw_data,q=1):

    ps = np.array(pSpectrum(raw_data))

    ps = ps/np.sum(ps)

    s = entropy(ps,q)

    return s

def normalize(vector):
    #vNorm = (vector - np.mean(vector))/np.std(vector)
    vNorm = (vector - np.median(vector))/np.std(vector)
    #vNorm = (vector)/np.std(vector)
    return vNorm


def binning(x,y,bins,log_10=False,confinter=5):
    '''makes a simple binning'''
     
    x = np.array(x);y = np.array(y)
    
    if isinstance(bins,int) or isinstance(bins,float):
        bins = np.linspace(np.min(x)*0.9,np.max(x)*1.1,bins)
    else:
        bins = np.array(bins)
        
    if log_10:
        bins = bins[bins>0]
        c = x > 0
        x = x[c]
        y = y[c]
        bins = np.log10(bins)
        x = np.log10(x)
        y = np.log10(y)

    Tbins = []
    Median = []
    Mean = []
    Sigma =[]
    Perc_Up = []
    Perc_Down = []
    Points=[]


    for i,ix in enumerate(bins):
        if i+2>len(bins):
            break
            
        c1 = x >= ix
        c2 = x < bins[i+1]
        c=c1*c2

        if len(y[c])>0:
            Tbins = np.append(Tbins,np.median(x[c]))
            Median =  np.append(Median,np.median(y[c]))
            Mean = np.append(Mean,np.mean(y[c]))
            Sigma = np.append(Sigma,np.std(y[c]))
            Perc_Down = np.append(Perc_Down,np.percentile(y[c],confinter))
            Perc_Up = np.append(Perc_Up,np.percentile(y[c],100 - confinter))
            Points = np.append(Points,len(y[c]))


    return {'bins' : Tbins, 
            'median' : Median, 
            'mean' : Mean, 
            'stdDev' : Sigma, 
            'percDown' :Perc_Down,
            'percUp' :Perc_Up,
            'nPoints' : Points}


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


def pullResponses(dic,treatment):
    r = dic[treatment]['responses']
    return r

def checkResponseProperNouns(dic,tol=0.3):
    
    if dic['responses'].has_key('r2'):
        key = 'r2'
    else:
         key = '2'
    
    ans = re.findall(r"[\w']+", ",".join(dic['responses'][key]['response']))
    rans = np.array(dic['responses'][key]['question']['rightAnswer'].keys())
    
    l = len(rans)
    lr = 0
    for a in ans:
        for ra in rans:
            d = Levenshtein.distance(str(a),str(ra))/float(len(ra))
            if d < tol:
                print a,ra
                lr += 1
    return float(lr)/l


def checkResponseCommonNouns(dic):
    if dic['responses'].has_key('r3'):
        key = 'r3'
    else:
         key = '3'
    
    ansIndex = dic['responses'][key]['response']['choices']
    ans = np.array(dic['responses'][key]['response']['input'])[np.array(map(int,ansIndex))-1]
    rans = np.array(dic['responses'][key]['question']['rightAnswer'])
    score = len(np.intersect1d(ans,rans))/float(len(rans))
    print score
    return ans,rans,score

def makeStatistics(dic):
    charNumber = "".join(dic['exp']['words'])
    t = dic['exp']['timestamps']
    duration = t[-1]-t[0]
    


def plotRateEntropy(json):
    time = json['exp']['timestamps']
    rate = json['exp']['rate']
    entropy = json['exp']['normalized_entropy']
    
    pl.figure(1,(8,18))
    pl.subplot(211)
    pl.plot(time,rate)
    pl.subplot(212)
    pl.plot(time,entropy)   
    
  
def rateVsLenWord(J,Jlist,treatment,deque=0,plot=False):

    if deque ==0:
        words = np.array(J[Jlist[treatment]]['exp']['words'])[:-1]
        lWords = np.array([len(word) for word in words])
        rate = 1./np.array(J[Jlist[treatment]]['exp']['rate'])
        dRate = np.diff(rate)/rate[:-1]*100#[1 + deque:]
        sEntropy = np.array(J[Jlist[treatment]]['exp']['normalized_entropy'][:-1])
        
        
    else: 
        words = np.array(J[Jlist[treatment]]['exp']['words'])[:-1][:-1 - deque]
        lWords = np.array([len(word) for word in words])
        rate = 1./np.array(J[Jlist[treatment]]['exp']['rate'])[1 + deque:]
        dRate = np.diff(rate)/rate[:-1]*100#[1 + deque:]
        sEntropy = np.array(J[Jlist[treatment]]['exp']['normalized_entropy'][:-1][1 + deque:])


        
    try:
        print J[Jlist[treatment]]['meta']['articleKey'],len(lWords),np.median(lWords),np.mean(lWords)
    except:
        print "no meta found",len(lWords),np.median(lWords),np.mean(lWords)
    
    
    #print len(words),len(lWords),len(rate)
    c = (lWords < 13)

    #B = binning(lWords[c],dRate[c],30)
    B = binning(lWords[c],sEntropy[c],30)
    fitB = S.linregress(B['bins'],B['mean'])
    
    
    
    #print fitB
    if plot:
        #pl.figure(1,(18,6))
        pl.subplot(131)
        pl.plot(rate)
        pl.xlabel("time [words]")
        pl.ylabel("rate [words/seconds]")
        
        
        pl.subplot(132)
        pl.plot(lWords,sEntropy,'.')
        pl.plot(B['bins'],B['mean'],'ro')
        pl.plot(lWords,lWords*fitB[0] + fitB[1],'r-',lw=2)
        pl.errorbar(B['bins'],B['mean'],yerr=B['stdDev'],color="red")
        #pl.fill_between(B[0],B[3],B[4],color="r",alpha=0.3)
        
        x0 = lWords
        y0 = np.zeros_like(x0)
        pl.plot(x0,y0,'k-' ,lw= 2)
        
        yVert = np.linspace(np.min(dRate),np.max(dRate),10)
        xVert = np.zeros_like(yVert) + np.mean(lWords)
        pl.plot(xVert,yVert,'k-' ,lw = 2)
        
        pl.xlabel("word length")
        #pl.ylabel("rate change [%]")
        pl.ylabel("Entropy")

        pl.subplot(133)
        #dRateChangeAroundLargeWords(lWords,dRate,minWlength=9,maxWlength=30,plot=True)
        dRateChangeAroundLargeWords(lWords,dRate,minWlength = 8,maxWlength= 30, plot=True)
        entropyChangeAroundLargeWords(lWords,sEntropy,minWlength = 8,maxWlength= 30, plot=True)
        #pl.ylim(-0.5,0.5)
        pl.ylabel("Normalized Entropy (green) / rate change (red)")
        
    return fitB


def dRateChangeAroundLargeWords(lWords,dRate,minWlength = 10,maxWlength= 30, plot=True):

    tWords = np.arange(len(lWords))
    c = (lWords >= minWlength)*(lWords < maxWlength)
    cBootstrap = lWords < 6 

    Xbootstrap = []
    Ybootstrap = []

    index = np.argwhere(c)
    l = len(index)


    lower_t = -15
    upper_t = 15

    j = 0
    maxIter = 100
    

    
    while j <= maxIter:
        
        if j < maxIter:
            index = np.argwhere(np.invert(c))
            index = range(len(tWords))
            index = np.argwhere(cBootstrap)
            
            np.random.shuffle(index)
            index = index[:l]
            
        elif j == maxIter: 
            index = np.argwhere(c)
            

        try:
            
            X = []
            Y = []
            
            for i,ix in enumerate(index):
                y = dRate[index[i] + lower_t:index[i] + upper_t]         
        
                x = tWords[index[i] + lower_t:index[i] + upper_t] - tWords[index[i]]
                X = np.append(X,x)
                Y = np.append(Y,y)
                
            B = binning(X,Y,30)
            
            Xbootstrap = np.append(Xbootstrap,B['bins'])
            Ybootstrap = np.append(Ybootstrap,B['mean'])
            
            j += 1
            #print j
        except:
            j += 1
            continue

    if plot:
        x0 = np.arange(lower_t,upper_t)
        y0 = np.zeros_like(x0)
        pl.plot(x0,y0,'k-')
        
        yVert = np.linspace(-0.5,0.5,10)
        xVert = np.zeros_like(yVert)
        pl.plot(xVert,yVert,'k-')
        
        
        Bbootstrap = binning(Xbootstrap,Ybootstrap,30,confinter=10)
        
        #print Bbootstrap
        
        #if j==maxIter:
        #pl.plot(Xbootstrap,Ybootstrap,'bo',alpha=0.05)
        pl.plot(Bbootstrap['bins'],Bbootstrap['mean'],'bo-',alpha=1)
        #pl.errorbar(Bbootstrap['bins'],Bbootstrap['mean'],yerr=Bbootstrap['stdDev'],color="red")
        pl.fill_between(Bbootstrap['bins'],Bbootstrap['percDown'],Bbootstrap['percUp'],color="b",alpha=0.2)
        
        pl.plot(B['bins'],B['mean'],'ro-')
        
        #pl.ylim(-0.5,0.5)
        pl.xlabel("time [word count]")
        pl.ylabel("rate change [%]")


def entropyChangeAroundLargeWords(lWords,sEntropy,minWlength = 9,maxWlength= 30, confinter = 10, plot=True):

    tWords = np.arange(len(lWords))
    c = (lWords >= minWlength)*(lWords < maxWlength) #Select large words
    cBootstrap = lWords < 3 # condition for selecting small words

    Xbootstrap = []
    Ybootstrap = []

    index = np.argwhere(c) #make index of large word positions
    l = len(index) #count number of large words

    lower_t = -15
    upper_t = 15

    j = 0
    maxIter = 100 #set the number of iterations for bootstrapping
    

    
    while j <= maxIter:
        
        if j < maxIter:
            #index = np.argwhere(np.invert(c))
            #index = range(len(tWords))
            index = np.argwhere(cBootstrap)
            
            np.random.shuffle(index)
            index = index[:l]
            
        elif j == maxIter: 
            index = np.argwhere(c)
            

        try:
            
            X = []
            Y = []
            LW = []
            
            for i,ix in enumerate(index):
                y = sEntropy[index[i] + lower_t:index[i] + upper_t]         
        
                x = tWords[index[i] + lower_t:index[i] + upper_t] - tWords[index[i]]
                lw = lWords[index[i] + lower_t:index[i] + upper_t]
                
                X = np.append(X,x)
                Y = np.append(Y,y)
                LW = np.append(LW,lw)
                
            B = binning(X,Y,30,confinter=confinter)
            BLW = binning(X,LW,30,confinter=confinter)
            
            #Xbootstrap = np.append(Xbootstrap,B['bins'])
            #Ybootstrap = np.append(Ybootstrap,B['mean'])
            
            if j < maxIter:
                Xbootstrap = np.append(Xbootstrap,B['bins'])
                Ybootstrap = np.append(Ybootstrap,B['mean'])
            
            j += 1
            #print j
        except:
            j += 1
            continue

    if plot:
        '''
        x0 = np.arange(lower_t,upper_t)
        y0 = np.zeros_like(x0)
        pl.plot(x0,y0,'k-')
        
        yVert = np.linspace(-0.5,0.5,10)
        xVert = np.zeros_like(yVert)
        pl.plot(xVert,yVert,'k-')
        '''
        
        Bbootstrap = binning(Xbootstrap,Ybootstrap,30,confinter=confinter)
        
        #pl.plot(Bbootstrap['bins'],Bbootstrap['mean'] - np.mean(B['mean']),'yo-',alpha=1)
        #pl.fill_between(Bbootstrap['bins'],Bbootstrap['percDown'] - np.mean(B['mean']),Bbootstrap['percUp'] - np.mean(B['mean']),color="y",alpha=0.2)
        #pl.plot(B['bins'],B['mean'] - np.mean(B['mean']),'go-')

        pl.fill_between(Bbootstrap['bins'],Bbootstrap['percDown'],Bbootstrap['percUp'],color="y",alpha=0.2)        
        pl.bar(BLW['bins'],BLW['mean']/np.max(BLW['mean'])*0.25,color='cyan',lw=0,alpha=0.5)
        pl.plot(Bbootstrap['bins'],Bbootstrap['mean'],'yo-',alpha=1)

        #pl.fill_between(B['bins'],B['percDown'],B['percUp'],color="g",alpha=0.2)
        pl.plot(B['bins'],B['mean'],'go-')
        
        #pl.ylim(-0.5,0.5)
        pl.xlabel("time [word count]")
        pl.ylabel("Entropy")



def entropyVsLenWord(J,Jlist,treatment,deque=0,plot=False):
    
    if deque ==0:
        words = np.array(J[Jlist[treatment]]['exp']['words'])#[:-1 - deque]
        lWords = np.array([len(word) for word in words])
        rate = 1./np.array(J[Jlist[treatment]]['exp']['rate'])#[1 + deque:]
        s = np.array(J[Jlist[treatment]]['exp']['entropy'])
    else: 
        words = np.array(J[Jlist[treatment]]['exp']['words'])[:-1 - deque]
        lWords = np.array([len(word) for word in words])
        rate = 1./np.array(J[Jlist[treatment]]['exp']['rate'])[1 + deque:]
        s = np.array(J[Jlist[treatment]]['exp']['entropy'])[1 + deque:]
        
    B = binning(lWords,s,30)
    fitB = S.linregress(B[0],B[1])
    
    
    if plot:
        #pl.subplot(121)
        #pl.plot(rate)

        #pl.subplot(122)
        pl.plot(lWords,s,'.')
        pl.plot(B['bins'],B['mean'],'ro')
        pl.plot(lWords,lWords*fitB[0] + fitB[1],'r-')
        pl.errorbar(B['bins'],B['mean'],yerr=B['stdDev'],color="red")
        #pl.fill_between(B[0],B[3],B[4],color="r",alpha=0.3)
        pl.xlabel("word length")
        pl.ylabel("entropy")
        
    return fitB
    
def crossLagCorr(x,y,lagspan=35):
    
    rho = []
    p = []
    L = range(-lagspan,lagspan)

    
    for l in L:
        if l==0:
            rho.append(S.spearmanr(x,y)[0])
            p.append(S.spearmanr(x,y)[1])
        elif l < 0:
             rho.append(S.spearmanr(x[-l:],y[:l])[0])
             p.append(S.spearmanr(x[-l:],y[:l])[1])
        else:
            rho.append(S.spearmanr(x[:-l],y[l:])[0])
            p.append(S.spearmanr(x[:-l],y[l:])[1])
            
    return np.array(L),np.array(rho),np.array(p)
    
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


def exploreVicinityLargeWords(J,Jlist,treatment):

    minWlength = 10
    maxWlength = 30

    words = np.array(J[Jlist[treatment]]['exp']['words'])[:-1]
    lWords = np.array([len(word) for word in words])
    rate = 1./np.array(J[Jlist[treatment]]['exp']['rate'])
    dRate = np.diff(rate)/rate[:-1]*100#[1 + deque:]
    sEntropy = np.array(J[Jlist[treatment]]['exp']['entropy'][:-1])
    timestamps = np.array(J[Jlist[treatment]]['exp']['timestamps'])[:-1]
    
    tWords = np.arange(len(lWords))
    c = (lWords >= minWlength)*(lWords < maxWlength)
    index = np.argwhere(c).flatten()
    #print index
    l = len(index)
    
    #print sEntropy[index].flatten()
    o = np.argsort(sEntropy[index].flatten())
    #print o
    #print sEntropy[index][o]
    #print o,index[o]
    #print np.mean(sEntropy[index]),np.mean(sEntropy[np.invert(c)])
        
    largeWordIndex = 7

    #colors = ['blue','blue','blue','red','red','red']

    pl.close(5)
    pl.figure(5,(10,10))
    pl.xlim(xmax = 10000)
    
    l = len(o[::2])
    
    for i,largeWordIndex in enumerate(o[::2]):
        
        #print index[largeWordIndex]
        
        '''Find time boundaries '''
        i1 = timestamps[index][largeWordIndex]
        i0 = i1 - 1
        s = sEntropy[index][largeWordIndex]
        #print i0,i1,s
    
        '''Pull raw signal'''
        tEEG = np.array(J[Jlist[treatment]]['eegData']['t'])
        rawsig = np.array(J[Jlist[treatment]]['eegData']['rawsig'])
        
        '''select raw signal and plot power spectrum'''
        cEEG = (tEEG >= i0)*( tEEG < i1)
        ps = pSpectrum(rawsig[cEEG])
        B = binning(range(len(ps)),ps,100)        
        pl.loglog(B['bins'],B['mean'],'-',label="%.2f"%s,color="r",lw = 0.35*(1 + 4*i/float(l)))

        print sEntropy[index][largeWordIndex],compute_entropy(ps,q=1)
    
    #pl.legend(loc=0)
    
    index = np.argwhere(np.invert(c))
    #index = range(len(tWords))
    #index = np.argwhere(cBootstrap)
            
    np.random.shuffle(index)
    index = index[:10]
    
    
    for i,normalWordIndex in enumerate(index):
        
        #print index[largeWordIndex]
        
        '''Find time boundaries '''
        i1 = timestamps[normalWordIndex]
        i0 = i1 - 1
        s = sEntropy[normalWordIndex]
        #print i0,i1,s
    
        '''Pull raw signal'''
        tEEG = np.array(J[Jlist[treatment]]['eegData']['t'])
        rawsig = np.array(J[Jlist[treatment]]['eegData']['rawsig'])
        
        '''select raw signal and plot power spectrum'''
        cEEG = (tEEG >= i0)*( tEEG < i1)
        ps = pSpectrum(rawsig[cEEG])
        B = binning(range(len(ps)),ps,100)        
        pl.loglog(B['bins'],B['mean'],'-',label="%.2f"%s,color="b")

        print sEntropy[normalWordIndex],compute_entropy(ps,q=1)
    
    #pl.legend(loc=0)

def explorePriorEntropy(J,Jlist,treatment):
    
    minWlength = 10
    maxWlength = 30

    words = np.array(J[Jlist[treatment]]['exp']['words'])[:-1]
    lWords = np.array([len(word) for word in words])
    rate = 1./np.array(J[Jlist[treatment]]['exp']['rate'])
    dRate = np.diff(rate)/rate[:-1]*100#[1 + deque:]
    sEntropy = np.array(J[Jlist[treatment]]['exp']['entropy'][:-1])
    timestamps = np.array(J[Jlist[treatment]]['exp']['timestamps'])[:-1]
    
    tWords = np.arange(len(lWords))
    c = (lWords >= minWlength)*(lWords < maxWlength)
    index = np.argwhere(c).flatten()
    
    
    '''Pull raw signal'''
    tEEG = np.array(J[Jlist[treatment]]['eegData']['t'])
    rawsig = np.array(J[Jlist[treatment]]['eegData']['rawsig'])
    
    print sEntropy[index[7]]
    ref_timestamp = index[7]

    
    pl.close(5)
    pl.figure(5,(10,10))
    pl.xlim(xmax = 10000)
    
    sAll = []
    
    for i in np.arange(1,11):
    
        s = sEntropy[ref_timestamp-i]
        
        '''Find time boundaries '''
        t_ref = timestamps[ref_timestamp-i]
        
        
        '''extract raw signal'''
        cEEG = (tEEG < t_ref)
        raw = rawsig[cEEG][-512:]
        
        ps = pSpectrum(raw)
        sAll.append(compute_entropy(ps,q=1))
        
        print sAll[-1],s
            
        B = binning(range(len(ps)),ps,100)        
        pl.loglog(B['bins'],B['mean'],'-',label="%.2f"%s,color="b")
    
    
    print normalize(sAll)