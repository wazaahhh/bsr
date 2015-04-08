import numpy as np
import time
import os
import random
import json
from entropy import compute_entropy,normalize
import threading

from readNeuroskyData import readMindwave
MW = readMindwave()
from bsrLib import bsr
bsr = bsr()

def blink5times():
    taskname = "Blink task"
    instruction = 'Blink when the word "blink" appears'
    
    print taskname
    print instruction
    
    try:
        input= raw_input("Press any key to continue")
    except NameError:
        pass
   
    blinkTimes = []
    MW.dumpBuffer()
    for b in range(5):
        blinkTimes.append(time.time())
        print "\n" * 10
        print "\t" *5, "blink" # (%s)"%blinkTimes[-1]
        print "\n" * 10
        time.sleep(0.25)        
        
        print "\n" * 30
        time.sleep(2)
        
        
    eegData = MW.dumpBuffer()
    blinkTimes = {'blinkTimes' : blinkTimes, 'eegData' : eegData}
        
    return blinkTimes


def restingState(duration=30):
    taskname = "Resting state"
    instruction = "Close you eyes, relax, and try not to think about anything for %s seconds"%duration
    
    print taskname
    print instruction
    
    try:
        input= raw_input("Press any key to continue")
    except NameError:
        pass   
    
    MW.dumpBuffer()
    print "<black screen>"
    print "\n" * 30
    
    time.sleep(duration)
    rState = MW.dumpBuffer()
    os.system('say "Open your eyes"')
    
    return {'eegData' : rState}


def doMath(iterations= 10, operation_duration = 2):
    taskname = "Mental Math"
    instruction = "Make mental math operations presented on the screen"

    print taskname
    print instruction
    
    try:
        input= raw_input("Press any key to continue")
    except NameError:
        pass  

    mathOps = {}
    
    MW.raw_data = []
    for i in range(iterations):
        n1 = random.randint(1,15)
        n2 = random.randint(1,15)
        mathOps[time.time()] = [n1,n2]        
        
        print "\n" * 10
        print "\t" *5, "%s x %s"%(n1,n2)
        print "\n" * 10
        time.sleep(operation_duration)
       
    eegData = MW.getRawEEG()
    return {'operations': mathOps,'eegData' : eegData} 

def readTextEnglish():
    
    readTextJson = json.loads(open("articles/backup/ObamaCybersecurity.json",'rb').read())    
    
    taskname = "Read Text"
    instruction = "Read in silence the following short text."
    print taskname
    print instruction  

    try:
        input= raw_input("Press any key to continue")
    except NameError:
        pass

    MW.dumpBuffer()
    print "%s \n Author:%s \n Source: %s"%(readTextJson['title'],readTextJson['author'],readTextJson['url'])
    print "%s \n\n"%(readTextJson['content'])

    try:
        input= raw_input("Press any key to continue")
    except NameError:
        pass

    readTxt = MW.dumpBuffer()
    
    return {'eegData' : readTxt}
# 
# 
# def RSVP(articleJson,treatment):
# 
#     taskname = "rsvp"
#     instruction = '''You will see words displayed one at the time at some varying speed. As much as you can, try to get the general meaning of the text and try to memorize important key words, as well as important people, places, organizations and institutions '''
# 
#     print taskname
#     print instruction
# 
#     try:
#         input= raw_input("Press any key to continue")
#     except NameError:
#         pass
# 
#     MW.raw_data = []
#     time.sleep(5)
#     J = bsr.showWords(articleJson,treatment)
#     eegData = MW.getRawEEG()
# 
#     return {'exp' : J,'eegData' : eegData}



def listArticles(folder="in_use",display=False):
    aDic = {}
    listA = os.listdir("articles/%s"%folder)
    
    try:
        rm = np.argwhere(np.array(listA)=='.DS_Store')[0]
        listA = np.delete(listA,rm)
    except:
        pass
        
    for i,article  in enumerate(listA):
        
        J = json.loads(open("articles/%s/%s"%(folder,article),'rb').read())
        aDic[i+1] = J
        if display:
            print "articles/%s/%s"%(folder,article)
            print "%s. %s by %s (%s)\n"%(i+1,J['title'],J['author'],J['url'])
    return aDic


def randomCommonNounFromList(max):
    l = np.random.randint(max)
    list = open("wordlists/common_words_cleaned",'r').read().splitlines()
    np.random.shuffle(list)
    return list[:l]


def question3(articleJson,max=6):
    textNouns = articleJson['nouns'].keys()
    np.random.shuffle(textNouns)    
    commonNouns = randomCommonNounFromList(max-1)
    wordlist = np.unique(commonNouns + textNouns[:max-len(commonNouns)])
    np.random.shuffle(wordlist)
    return list(wordlist)


def generateQuestions(articleJson):
    return [{'question':'Please tell us briefly about the article you have just read (max. 100 words).', 'type':'free_response'},
    {'question':'Can you remember people, places, organizations and institutions mentioned in the article? (List one per line).', 'type':'free_recall'},
    {'question':'Which of these words appeared in the text?', 'type':'multiple_choice', 'choices':question3(articleJson,max=6)}]

def sendQuestions(self,questions):
    self.postToServer('/show_questions', json.dumps(questions))



class bsr():
    def __init__(self):
        self.onText = True
        
        self.initRate = 0.125
        self.currentRate = self.initRate
        self.rate = [self.initRate]
        self.words = ['x']
        self.time = [0]
        
        '''BSR parameters'''
        self.entropy_window = 256
        self.deque = 10
        self.adaptivity = -0.005
        self.currentEntropy = 0
        self.entropy = [0] #list(np.random.rand(30)/100.)
        self.normalized_entropy = [0]

        '''AR parameters'''
        self.ARc=0.150
        self.ARphi=0.075
        self.ARsigma=0.001

    
    def AR1(self):
        ar1 = (1.) * self.currentRate + np.random.normal(scale=self.ARsigma)
        if ar1 < 0:
            ar1 = -ar1
        return ar1


    def getCurrentEntropy(self):
        #print MW.raw_data[-10:]
        rawEEG = zip(*MW.raw_data)[2][-self.entropy_window:]
        
        try:
            if np.median(rawEEG) > 150:
                self.entropy.append(self.entropy[-1])
            else:
                #print rawEEG
                #print compute_entropy(rawEEG,1)
                self.entropy.append(compute_entropy(rawEEG,1))
            
            self.normalized_entropy.append(normalize(self.entropy[-self.deque:])[-1])                
            self.currentEntropy = self.normalized_entropy[-1]
        except:
            pass

    def updateRate(self,treatment):
        if treatment=="bsr+":
            self.getCurrentEntropy()
            self.currentRate = self.currentRate*(1 + (self.adaptivity*self.currentEntropy))
        
        elif treatment=="bsr-":
            self.getCurrentEntropy()
            self.currentRate =self.currentRate*(1 - (self.adaptivity*self.currentEntropy))
        
        elif treatment=="ar1":
            self.currentRate = self.AR1()
        
        elif treatment=="cst":
            self.currentRate = self.currentRate
        
    def RSVP(self,articleJson,treatment):
        
        taskname = "rsvp"
        instruction = '''You will see words displayed one at the time at some varying speed. As much as you can, try to get the general meaning of the text and try to memorize important key words, as well as important people, places, organizations and institutions '''
    
        print taskname
        print instruction
    
        try:
            input= raw_input("Press any key to continue")
        except NameError:
            pass

        self.currentRate = self.initRate
        self.entropy = [0]
        self.normalized_entropy = [0]
        self.rate = [self.initRate]
        self.words = ['x']
        self.time = [0]

        
        txt = articleJson['content']
        wordListRead = txt.split()
        
        self.printWord('x')
        time.sleep(2)
        
        
        for word in wordListRead:            
            self.updateRate(treatment)
            self.rate.append(self.currentRate)
            self.words.append(word)
            self.time.append(time.time())
            
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
        
        #print self.time
        t0 = self.time[1]
        t = [ item - t0 for item in self.time]
        t = t[1:]
        
        
        eegData = MW.getRawEEG()
        
        expDic  = {'exp': {'rate': self.rate,'entropy' : self.entropy,'normalized_entropy' : self.normalized_entropy,'words' : self.words, 'timestamps' : t,'t0':t0},'eegData':eegData}
        return expDic
    
        '''
        MW.raw_data = []
        time.sleep(5)
        J = self.showWords(articleJson,treatment)
        eegData = MW.getRawEEG()
        return {'exp' : J,'eegData' : eegData}
        '''
    
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
    

    def sendWord(self,word):
        self.postToServer('/show_word', json.dumps({'word': word}))

    '''
    def runTest(self):
        
    
        start = time.time()
        now = time.time()
    
        tEEG = threading.Thread(target=MW.readRawEEG)
        tEEG.daemon = True
        tEEG.start()
    
    
        MW.tryConnection(verbose = True)
    
        time.sleep(2)
        
        self.getCurrentEntropy()
        print self.currentEntropy
        time.sleep(2)
        bsr.getCurrentEntropy()
        print bsr.currentEntropy
        time.sleep(2)
        bsr.getCurrentEntropy()
        print bsr.currentEntropy
    '''


    


def runTest():
    tEEG = threading.Thread(target=MW.readRawEEG)
    tEEG.daemon = True
    tEEG.start()

    time.sleep(5)
    MW.connectionCheck()
    time.sleep(2)
    MW.qualityCheckLoop()

    time.sleep(5)
    aDic = listArticles(folder="in_use")
    treatment = "bsr+"
    J= RSVP(aDic[1],treatment)
    return J



    
if __name__ == '__main__':
    print "blah"
    
    J = runTest()
    
    
    
