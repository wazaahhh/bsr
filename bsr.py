
import numpy as np
import csv
import time
import threading
from entropy import compute_entropy,normalize
#import boto
from uuid import getnode as get_mac
from datetime import datetime
from mindwave_mobile import ThinkGearProtocol, ThinkGearRawWaveData, ThinkGearEEGPowerData, ThinkGearPoorSignalData, ThinkGearAttentionData, ThinkGearMeditationData
from textPrepare import *
import json
import zlib
import requests
import os
from nltk.tokenize import word_tokenize
from nltk.tag import pos_tag
from nltk import FreqDist


def uplodJson(Json,textId,compress=False):
    now = datetime.utcnow().strftime("%Y/%m/%d/%H%M%S")
    if compress:
        extension=".zlib"
        Json = zlib.compress(json.dumps(Json))
    else:
        extension=""
        Json = json.dumps(Json)
    
    #key = bucket.new_key("/bsr/%s/%s/%s.json%s"%(get_mac(),textId,now,extension))
    #key.set_contents_from_string()
    r = requests.put('http://brainspeedr.s3.amazonaws.com/bsr/%s/%s/%s.json%s'%(get_mac(),textId,now,extension), data=Json)


def listArticles(folder):
    aDic = {}
    listA = os.listdir("articles/%s"%folder)
    
    try:
        rm = np.argwhere(np.array(listA)=='.DS_Store')[0]
        listA = np.delete(listA,rm)
    except:
        pass
        
    for i,article  in enumerate(listA):
        print "articles/%s/%s"%(folder,article)
        J = json.loads(open("articles/%s/%s"%(folder,article),'rb').read())
        aDic[i+1] = J
        print "%s. %s by %s (%s)\n"%(i+1,J['title'],J['author'],J['url'])
    return aDic
    
def selectArticles(folder="in_use"):        
        aDic = listArticles(folder)
        print "choose one of the articles above (%s to %s):"%(1,len(aDic))
        
        #recentTexts = np.array([r for r in csv.reader(open("recentTexts.csv",'rb'))])
        #print "\n"*30
        #print "choose one of the text below by entering a number or paste URL:"
        #if len(recentTexts)>0:
        #    for r,rx in enumerate(recentTexts[-10:]):
        #        print '%s) %s '%(r+1,rx[0])
        #else:
        #    print "no recent text available"
        
        input = int(raw_input("\nChoice : ")) 
        cond = input < 1 or input > len(aDic)
        
        while cond:
            print "incorrect choice, try again:"
            input = int(raw_input("\nChoice : "))
            cond = input < 1 or input > len(aDic)
           
        
        print "your choice : %s by %s (%s) \nlet's get started..."%(aDic[input]['title'],aDic[input]['author'],aDic[input]['url'])
        return aDic[input]


def findCommonNouns(aDic,minFreq=2):
    #dicTypeWords = {"propernouns":'NNP','nouns':'NN'}
    tagged_sent = pos_tag(word_tokenize(aDic['content']))
    
    wordDic = {}
    fdist= FreqDist(tagged_sent)
    for i,ix in enumerate(tagged_sent):
        print i,ix
        if ix[1] == 'NN' and fdist[ix] >=minFreq:            
            try:
                pos = wordDic[ix[0]]['pos']
                pos.append(i)
            except:
                pos = [i]
            wordDic[ix[0]] = {'pos':pos,'freq':fdist[ix]} 
    return wordDic

def commmonNounsList(minFreq=5,storeFile=False):
    folder = "backup"
    listA = os.listdir("articles/%s"%folder)
    
    list = []
    
    for article in listA:
        aDic = json.loads(open("articles/%s/%s"%(folder,article),'rb').read())
        l = findCommonNouns(aDic,minFreq=minFreq)
        list += l
      
    list = np.array(zip(*list))
    l2 = np.array(map(int,list[1]))
    o = np.argsort(l2)[::-1]    
    list = np.array(zip(*list))[o]
    
    if storeFile:
        output=open("wordlists/common_words",'wb')
        output.write("\n".join(np.unique(zip(*list)[0])))
        output.close()
    return list


def randomCommonNounFromList(max):
    l = np.random.randint(max)
    list = open("wordlists/common_words_cleaned",'r').read().splitlines()
    np.random.shuffle(list)
    return list[:l]


def findWordTypeSeries(tagged_sent,wordTypeSeries):
    from numpy.lib.stride_tricks import as_strided
        
    wordTypeSeries = np.array(wordTypeSeries)
        
    typeSeries = tagged_sent[1]
    
    a_view = as_strided(typeSeries, shape=(len(typeSeries) - len(wordTypeSeries) + 1, len(wordTypeSeries)),strides=(typeSeries.dtype.itemsize,) * 2)
    
    index = np.where(np.all(a_view == wordTypeSeries, axis=1))[0]

    output = {}

    for i in index:
        try:
            output[' '.join(tagged_sent[0][i:i+len(wordTypeSeries)])].append(i)
        except:
            output[' '.join(tagged_sent[0][i:i+len(wordTypeSeries)])] = [i]
 
    return output
 
 
def findProperNouns(aDic,minFreq=1):
    '''find all series of words in a text, following a series of types as tagged by "pos_tag" in nltk'''
    #types = [['NNP'],['NNP','NNP'],['NNP','IN','NNP'],['NNP','IN','NNP','NNP']]
    types = [['NNP']] 
    
    textString = aDic['content']
    
    tagged_sent = np.array(zip(*pos_tag(word_tokenize(textString))))
 
    dicIndexes = {}
    listLength = []
 
    wordDic = {}
 
    for type in types:
        dic = findWordTypeSeries(tagged_sent,type)
        for item in dic.iteritems():
            if len(item[1]) >= minFreq:
                wordDic[item[0]] = {'freq':len(item[1]), 'pos':item[1]}        
    return wordDic

def question3(aDic,max=6):
    textNouns = aDic['nouns'].keys()
    np.random.shuffle(textNouns)    
    commonNouns = randomCommonNounFromList(max-1)
    wordlist = commonNouns + textNouns[:max-len(commonNouns)]
    np.random.shuffle(wordlist)
    return wordlist

class BSR():
    
    def __init__(self):
        self.port = '/dev/tty.MindWaveMobile-DevA'
        self.entropy_window = 256
        self.raw_log = []
        self.attention_esense= None
        self.meditation_esense= None 
        self.eeg_power= None 
        self.signal_quality = 0
        self.start_time = None
        self.end_time = None
        self.timediff = None
        self.currentEntropy = 0
        self.entropy = [0] #list(np.random.rand(30)/100.)
        self.onText = True
        self.poorSignal = 100
        self.deque = 10
        self.normalized_entropy = [0]
        self.currentRate = 0.125
        self.adaptivity = -0.005
        self.Json = {}
    
#    def selectWords(self):
#        wordList = text1.split()
#        unique,count = np.unique(wordList,return_counts=True)        
#        lengths = np.array([len(i) for i in unique])
#        c = (count <= 5)*(lengths > 5)
#        return unique[c]

    def printWord(self,word):
        '''
        print "\n" * 10
        print "\t" *5, "%s"%(word)
        #print "\t  " *4, "(%.2f,%.0f)"%(self.currentEntropy,self.currentRate)
        print "\n" * 10
        '''
        print "\n" * 5
        print "\t" *3, "%s"%(word)
        print "\t" *3, "(%.3f)"%(self.currentRate)
        print "\n" * 5


    def AR1(self,c=0.150,phi=0.075,sigma=0.001):
        return (1.) * self.currentRate + np.random.normal(scale=sigma)
        

    def updateRate(self,treatment):
        if treatment=="bsr":
            return self.currentRate*(1 + (self.adaptivity*self.currentEntropy))
        elif treatment=="AR":
            return self.AR1()
        else:
            return self.currentRate


    def showWords(self,articleJson,treatment):
        txt = articleJson['content']
        wordListRead = txt.split()
        time.sleep(5)
        
        for word in wordListRead:            
            self.currentRate = self.updateRate(treatment)
            
            if word[-1] in [",","-"]:
                self.printWord(word)
                time.sleep(self.currentRate*1.5)
            elif word[-1] in [".",";",":"]:
                self.printWord(word)
                time.sleep(self.currentRate*3)
            elif word[-1]=="|":
                self.printWord(word[:-1])
                time.sleep(self.currentRate*4)
            else:
                self.printWord(word)
                time.sleep(self.currentRate)

    

    def experiment(self):
        articleJson = selectArticles()
        self.showWords(articleJson,treatment)
        
    
    def readEEG(self):
        
        Median = []
        Std = []
        for pkt in ThinkGearProtocol(self.port).get_packets():
            #print pkt
            for d in pkt:
 
                if isinstance(d, ThinkGearPoorSignalData):
                    self.signal_quality += int(str(d))
                    self.poorSignal = int(str(d))
                    #print self.poorSignal
                    
                if isinstance(d, ThinkGearAttentionData):
                    self.attention_esense = int(str(d))
 
                if isinstance(d, ThinkGearMeditationData):
                    self.meditation_esense = int(str(d))
 
                if isinstance(d, ThinkGearEEGPowerData):
                    # this cast is both amazing and embarrassing
                    self.eeg_power = eval(str(d).replace('(','[').replace(')',']'))
 
                if isinstance(d, ThinkGearRawWaveData): 
                    # record a reading
                    # how/can/should we cast this data beforehand?
                    self.raw_log.append(float(str(d))) 
                    
                    if len(self.raw_log) == self.entropy_window:
                        
                        Median.append(np.median(self.raw_log))
                        Std.append(np.std(self.raw_log))              
                        
                        if Median[-1] > 150:
                            self.entropy.append(self.entropy[-1])
                        else:
                            self.entropy.append(compute_entropy(self.raw_log,1))
                        
                        self.normalized_entropy.append(normalize(self.entropy[-self.deque:])[-1])
                        '''          
                        print "raw values: median: %.2f (medianM = %.2f), std: %.2f (medianStd = %.2f) " %(Median[-1],np.median(Median[-100:]),Std[-1],np.median(Std[-100:]))                          
                        print " entropy : %.3f (mean: %.3f, median: %.3f, std: %.3f)"%(self.entropy[-1],np.mean(self.entropy[-self.deque:]),np.median(self.entropy[-self.deque:]),np.std(self.entropy[-self.deque:]))
                        print "normalized entropy: %.3f (mean: %.3f, std : %.3f)"%(self.normalized_entropy[-1],np.mean(self.normalized_entropy[-100:]),np.std(self.normalized_entropy[-100:]))
                        print "\n"
                        '''
                        self.currentEntropy = self.normalized_entropy[-1]
                        #print self.currentEntropy
                        self.raw_log = []

            if self.onText == False:
                break
    

    
    def run(self):
        #S3connectBucket(bucketName)
        tEEG = threading.Thread(target=bsr.readEEG)
        tEEG.daemon = True
        tEEG.start()
        
        #try:
        
        Json = bsr.experiment()
        return Json
        #except:
        #    print "program terminated"

if __name__ == '__main__':
    
    global  bucketName
    bucketName = "brainspeedr"
    
    global onText    
    global questions
    questions = 3
    
    global Json
        
    global treatment
    treatment = "constant"
    
    bsr = BSR()
    #bsr.readEEG()
    
    #Json = bsr.run()
#    '''
    
        #print bsr.onText
 #   '''
        