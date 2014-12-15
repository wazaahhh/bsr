
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
        self.currentSpeed = 250
        self.adaptivity = 0.01
        self.Json = {}
    
#    def selectWords(self):
#        wordList = text1.split()
#        unique,count = np.unique(wordList,return_counts=True)        
#        lengths = np.array([len(i) for i in unique])
#        c = (count <= 5)*(lengths > 5)
#        return unique[c]

    def updateRate(self):
        return self.currentSpeed*(1 + (self.adaptivity*self.currentEntropy))

    def showWords(self,wordListRead):
                
        self.currentSpeed = float(raw_input('Choose your baseline speed (in milliseconds between two words): '))
        self.adaptivity = float(raw_input('Choose your adaptivity (between -0.02 and 0.02): '))
        
        self.Json['input']['baseline'] = self.currentSpeed
        self.Json['input']['adaptivity'] = self.adaptivity
        self.Json['input']['tStart'] = time.mktime(datetime.now().timetuple())
        
        '''clear screen'''
        print "\n" * 50
        time.sleep(5)
        
        words = []
        baseline = []
        entropy = []
        
        for word in wordListRead:

            self.currentSpeed = self.updateRate()
            
            print "\n" * 10
            print "\t" *5, "%s"%(word)
            #print "\t  " *4, "(%.2f,%.0f)"%(self.currentEntropy,self.currentSpeed)
            print "\n" * 10
                        
            time.sleep(self.currentSpeed/1000.)
    
            words.append(word)
            baseline.append(self.currentSpeed)
            entropy.append(self.entropy)
            
        self.onText = False
    
        return {'words' : words, 'baseline' : baseline, 'entropy' : entropy}

    
    def readEEG(self):
        
        Median = []
        Std = []
        
        for pkt in ThinkGearProtocol(self.port).get_packets():
            
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




    def experiment(self):
        
        recentTexts = np.array([r for r in csv.reader(open("recentTexts.csv",'rb'))])
        print "choose one of the text below by entering a number or paste URL:"
        if len(recentTexts)>0:
            for r,rx in enumerate(recentTexts[-10:]):
                print '%s) %s (URL: %s)'%(r+1,rx[0],rx[1])
        else:
            print "no recent text available"
            
        input = raw_input("choice : ")
        try:
            iInt = int(input)
            input = iInt
        except:
            iInt = None
            pass
        
        
        self.Json['input'] = {'txtUrl' : input}
        

        '''Determine if URL or Text, and process accordingly'''
        
        if isinstance(input,int):
            input = recentTexts[-input][1]
            
        if input[:10] == "http://www" or input[:11] =="https://www":
            try:
                html = retrieveHtml(input)
            except:
                print "webpage could not be retrieved"
            
            try:
                dicText = cleanHtmlToText(html)
                dicText = prepareText(dicText)
            except:
                print "problem cleaning html or preparing dicText"
                
        else:
            try:
                dicText = prepareText({'text' : input})
            except:
                print "problem preparing dicText"

        
        self.Json['text'] = dicText
        
        
        '''Show words'''
        dicShowWords = self.showWords(dicText['wordListRead'])
        self.Json['showWords'] = dicShowWords
        
        '''Questions'''
        dicQ = selectWords(dicText['wordList'],questions,countBoundaries=[0,5],lenBoundaries=[5,100])
        
        dicA = {}
        
        for k,key in enumerate(dicQ.keys()):
            print "Question %s / %s "%(k+1,len(dicQ))
            dicA[key] = raw_input('how many times the word "%s" has appeared in the text?  '%key)
            
        
        dicQA = {'Q' : dicQ ,'A' : dicA}
        
        self.Json['QA'] = dicQA
        self.Json['input']['tEnd'] = time.mktime(datetime.now().timetuple())
        
        if not isinstance(iInt,int):
            rTxtFiles = open("recentTexts.csv",'ab+')
            rTxtFiles.write("%s,%s\n"%(self.Json['text']['title'],self.Json['input']['txtUrl']))
            rTxtFiles.close()
        
        try:
            uplodJson(self.Json,re.sub(" ","",self.Json['text']['title']),compress=False)
            print "results successfully uploaded"
            return self.Json
        except:
            print "failed uploading results"
            return self.Json
    
    
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
    
    bsr = BSR()
    
    #bsr.readEEG()
    
    Json = bsr.run()
#    '''
    
        #print bsr.onText
 #   '''
        