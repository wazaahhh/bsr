import numpy as np
import time
import os
import random
import json
from entropy import compute_entropy,normalize
import threading
import re
import requests
from getTerminalSize import getTerminalSize

import logging
logging.getLogger("requests").setLevel(logging.WARNING)

from readNeuroskyData import readMindwave
MW = readMindwave()
#from bsrLib import bsr
#bsr = bsr()

# global articles
# articles = ['bigPolluter',
#          'emojiShortened',
#          'indianFood',
#          'marsOneShortened',
#          'Ohmconnect',
#          'pressFreedomUS']


# def listArticles(folder="in_use",display=False):
#     aDic = {}
#     listA = os.listdir("articles/%s"%folder)
#     
#     if '.DS_Store' in listA: listA.remove('.DS_Store')
#         
#     for i,article  in enumerate(listA):
#         print i,article
#         J = json.loads(open("articles/%s/%s"%(folder,article),'rb').read())
#         aDic[i+1] = J
#         if display:
#             print "articles/%s/%s"%(folder,article)
#             print "%s. %s by %s (%s)\n"%(i+1,J['title'],J['author'],J['url'])
#     return aDic

 
global articles
articles = ['bigPolluter',
         'emojiShortened',
         'indianFood',
         'marsOneShortened',
         'Ohmconnect',
         'pressFreedomUS']


def getArticlesFromS3():
    aDic = {}
    
    for i,article  in enumerate(articles):
        #print i+1,article
        r = requests.get('http://brainspeedr.s3.amazonaws.com/articles/in_use/%s.json'%article)
        if r.ok:
            J = json.loads(r.text)
            aDic[article] = J
    return aDic

global aDic
aDic = getArticlesFromS3()  

def listArticles(articles):
    descriptions = []
    keys = []
    for (key,articleJson) in aDic.items():
        if key in articles:
            descriptions.append("%s, by %s"%(articleJson['title'],articleJson['author']))
            keys.append(key)
        else:
            continue
        
    return keys,descriptions

def showArticleList(articles):
    keys,description = listArticles(articles)
    index = range(len(keys))
    random.shuffle(index)
    
    for i,ix in enumerate(index):
        #print "\n"
        niceTextDisplay("%s. %s"%(i+1,description[ix]),lineSleep=0.1)

    #print "\n"
    try:
        input= raw_input("Choose a text (1 to %s): "%len(index))
    except NameError:
        pass
      
    return keys[index[int(input)-1]]
#def chooseArticle(articles):
    
    
    
            

def niceTextDisplay(text,lineSleep=1):
    L = ""
    for w in text.split():
        if len(L) + len(w) < getTerminalSize()[0]-1:
            L += "%s "%w
        else:
            print L
            time.sleep(lineSleep)
            L = w + " "
    print L


def showWord(str):
    w,h = getTerminalSize()
    os.system('clear')
    print "\n" * int((h-2)/2)
    print " " * int((w-len(str))/2), str 
    #print "\n" * int((h)/2-4)


def blink5times():
    taskname = "Blink task"
    instruction = 'Blink when the word "blink" appears'
    
    #print taskname
    print instruction
    
    try:
        input= raw_input("Press any key to continue")
    except NameError:
        pass
    
    os.system("clear")
    showWord("x")
    time.sleep(2)
    os.system("clear")
    time.sleep(1)

    
    blinkTimes = []
    MW.dumpBuffer()
    for b in range(5):
        blinkTimes.append(time.time())
        showWord('blink')
        time.sleep(0.25)        
        
        print "\n" * 30
        time.sleep(2)
        
        
    eegData = MW.dumpBuffer()
    blinkTimes = {'blinkTimes' : blinkTimes, 'eegData' : eegData}
        
    return blinkTimes

def restingStateOpenEyes(duration=15):
    taskname = "Resting state open eyes"
    instruction = "Focus on the mark for %s seconds"%duration
     
    #print taskname
    print instruction
     
    try:
        input= raw_input("Press any key to continue")
    except NameError:
        pass   
     
    MW.dumpBuffer()
    os.system("clear")
    showWord("x")
    #print "\n" * 30
     
    time.sleep(duration)
    rState = MW.dumpBuffer()
    #os.system("say 'wake up!'")
     
    return {'eegData' : rState}


def restingStateClosedEyes(duration=15):
    taskname = "Resting state closed eyes"
    instruction = "Close you eyes, relax, and focus on your breathing for %s seconds"%duration
    
    #print taskname
    print instruction
    
    try:
        input= raw_input("(Press any key to continue)")
    except NameError:
        pass   
    
    MW.dumpBuffer()
    os.system("clear")
    
    time.sleep(duration)
    rState = MW.dumpBuffer()
    os.system("say 'wake up!'")
    
    return {'eegData' : rState}



def doMath(iterations= 10, operation_duration = 2.3):
    taskname = "Mental Math"
    instruction = "Make mental math operations presented on the screen"

    #print taskname
    print instruction
    
    try:
        input= raw_input("(Press any key to continue)")
    except NameError:
        pass  

    mathOps = {}
    
    MW.raw_data = []
    for i in range(iterations):
        n1 = random.randint(1,15)
        n2 = random.randint(1,15)
        mathOps[time.time()] = [n1,n2]        
        showWord("%s x %s"%(n1,n2))
        #print "\n" * 10
        #print "\t" *5, "%s x %s"%(n1,n2)
        #print "\n" * 10
        time.sleep(operation_duration)
       
    eegData = MW.getRawEEG()
    return {'operations': mathOps,'eegData' : eegData} 

def readTextEnglish():
    
    readTextJson = json.loads(open("articles/ObamaCybersecurityShortened.json",'rb').read())    
    
    taskname = "Read Text"
    instruction = "Read in silence the following short text."
    #print taskname
    print instruction  

    try:
        input= raw_input("(Press any key to continue)")
    except NameError:
        pass

    
    MW.dumpBuffer()
    os.system("clear && printf '\e[3J'")
    #print "%s \n Author:%s \n Source: %s"%(readTextJson['title'],readTextJson['author'],readTextJson['url'])
    #text = "%s \n\n"%(re.sub("\| ","\n",readTextJson['content']))
    text = readTextJson['content']
    #print "\n"
    text = re.sub("\|","",text)
    #for p in text.split("|"):
    niceTextDisplay(text)

    try:
        input= raw_input("(Press any key to continue)")
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



def randomCommonNounFromList(max):
    l = np.random.randint(max)
    list = open("wordlists/common_words_cleaned",'r').read().splitlines()
    np.random.shuffle(list)
    return list[:l]

def printIntroInstructions():
        print "\n"
        niceTextDisplay('''The brain speed reader experiment is about to start. 
                    Please make sure that you have paired the Neurosky Mindwave on your computer.''',lineSleep=0.2)
        print "\n" 
        niceTextDisplay('''If you have not yet connected Neurosky Mindwave, please follow the following steps:''',lineSleep=0.2)
        niceTextDisplay('''1. Select the bluetooth menu (in Settings),''',lineSleep=0.2)
        niceTextDisplay('''2. Select "Set up bluetooth device,''',lineSleep=0.2)
        niceTextDisplay('''3. Press "on/pair" button on the Neurosky Mindwave headset,''',lineSleep=0.2)
        niceTextDisplay('''4. When the Neurosky Mindwave appears on the bluetooth menu, 
        select it, click "continue" and follow the next steps,''',lineSleep=0.2)
        niceTextDisplay('''5. Place the headset on your head, with the sensors on your left forehead.''',lineSleep=0.2)
        print "\n"
        input= raw_input("(Press any key to continue)")


def printRSVPinstructions(manualChoice=False):
    niceTextDisplay('''You have successfully completed the preliminary tasks.''',lineSleep=0.2)
    print "\n"
    if manualChoice==False:
        niceTextDisplay('''We turn now to the "brain speed reader" experiment. You will be presented a list
        of texts to choose from, as well as a brain speed reader treatment.''',lineSleep=0.2)
        print "\n"
        niceTextDisplay('''After each text you will be asked to answer 5 short questions:''',lineSleep=0.2)
    else:
        niceTextDisplay('''Now we turn to the "brain speed reader" experiment. You will be presented some articles using Rapid Serial Visual Presentation (RSVP) at varying speed.''')
        print "\n"
        niceTextDisplay('''After each text you will be asked to answer 5 short questions:''',lineSleep=0.2)
         
    niceTextDisplay('''1: Summarize article you have just read.''',lineSleep=0.2)
    niceTextDisplay('''2: Recall people, places, organizations and institutions mentioned in the article.''',lineSleep=0.2)
    niceTextDisplay('''3: Identify common words that have appeared in the text.''',lineSleep=0.2)
    niceTextDisplay('''4: Reading comfort on a scale from 0 to 10.''',lineSleep=0.2)
    niceTextDisplay('''5: Attention level on a scale from 0 to 10.''',lineSleep=0.2)
    print "\n"
    input= raw_input("(Press any key to continue)")

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
    {'question':'Which of these words appeared in the text?', 'type':'multiple_choice', 'choices':question3(articleJson,max=6)},
    {'question':'How comfortable did you feel, when speed reading this text (on a scale from 0 to 10)?', 'type':'multiple_choice_scale'},
    {'question':'What was your level of attention, when speed reading this text (on a scale from 0 to 10)?', 'type':'multiple_choice_scale'}
    ]

 
def showQuestionsTUI(articleJson):
    '''asks questions on the terminal user interface (TUI)'''
    
    questions = generateQuestions(articleJson)
    for i,q in enumerate(questions):
        
        os.system("clear && printf '\e[3J'")
        print "Question %s/%s" %(i+1,len(questions)) 
        
        
        if q['type'] == 'free_response':
            try:
                niceTextDisplay('Please tell us briefly about the article you have just read (max. 100 words) :')
                print "(Press Enter to go to next question.)"
                os.system("tput cnorm")
                r1start = time.time()
                response1 = raw_input()
                r1end = time.time()
                os.system("tput civis")
                print "\n\n"
            except NameError:
                pass

        if q['type'] == 'free_recall':
            try:
                niceTextDisplay('Can you remember people, places, organizations and institutions mentioned in the article?')
                print "(Enter names separated by commas and Press Enter to go to next question.)"
                os.system("tput cnorm")
                r2start = time.time()
                response2 = raw_input()
                r2end = time.time()
                os.system("tput civis")
                print "\n\n"
                
            except NameError:
                pass
        
        if q['type'] == 'multiple_choice':
            try:
                print 'Which of these words appeared in the text?'
                niceTextDisplay('(Enter comma separated numbers corresponding to words found in the text. Press Enter to go to next question.)')
                for i,c in enumerate(q['choices']):
                    print "%s. %s"%(i+1,c)
                print "\n"
                os.system("tput cnorm")
                r3start = time.time()
                response3 = {'input': q['choices'],"choices" : raw_input().split(",")}
                r3end = time.time()
                os.system("tput civis")
                print "\n\n"
            except NameError:
                pass
        
        if q['type'] == 'multiple_choice_scale':
            try:
                print "%s. Press Enter to go to next task." % q['question']
                #print '(Enter comma separated numbers corresponding to words found in the text. Press Enter to finish.)' 
                os.system("tput cnorm")
                r4start = time.time()
                response4 = raw_input()
                r4end = time.time()
                os.system("tput civis")
                print "\n\n"
                print "\n\n"
            except NameError:
                pass
    
    return {'r1' : {'t0': r1start, 't1' : r1end, 'response' : response1}, 
            'r2' : {'t0': r2start, 't1' : r2end, 'response' : response2.split(",")},
            'r3' : {'t0': r3start, 't1' : r3end, 'response' : response3},
            'r4' : {'t0': r4start, 't1' : r4end, 'response' : response4}
            }
    
   
   
def generateFinalQuestions(texts):   
    questions = [{"question" : "Please rank the articles you just read, by level of comfort:","choices" : [aDic[t]['title'] for t in texts],'type':'ordered_choice'},
                 {"question" : "Please rank the articles by level of attention.","choices" : [aDic[t]['title'] for t in texts],'type':'ordered_choice'},
                 {"question" : "What is your gender?", "choices": ["Female","Male"],'type':'unique_choice'},
                 {"question" : "How old are you (years since birth)?", 'type':'free_response'},
                 {"question" : "Is English a native language for you?", "choices": ["Yes","No"],'type':'unique_choice'},
                 {"question" : "What is the highest academic degree you have achieved?", "choices": ["High School","Bachelor","Master","PhD"],'type':'unique_choice'},
                 {"question" : "Are you left-handed?", "choices": ["Right-handed","Left-handed","Ambidexterous"],'type':'unique_choice'},
                 {"question" : "Do you suffer any reading-related disabilities (e.g. dyslexia)?", "choices": ["Yes","No","I don't know"],'type':'unique_choice'},
                 {"question" : "Do you suffer any form attention disorder (e.g., ADD, ADHD)?", "choices": ["Yes","No","I don't know"],'type':'unique_choice'},
                 {"question" : "Do you take any psychotropic drugs (e.g. anti-depressants, psycho-stimulants, sleeping pills)?", "choices": ["Yes","No","Maybe"],'type':'unique_choice'},
                 {"question" : "Have you ever practiced any speed-reading or mental calculation techniques?", "choices": ["Yes","No","I don't remember"],'type':'unique_choice'}
                 ]

    return questions


def multipleChoiceQuestion(listChoices):
    os.system("tput cnorm")
    for i,c in enumerate(listChoices):
        print "%s. %s"%(i+1,c)
        
    l = len(listChoices)
    
    r = raw_input("(Enter any value between 1 and %s) : "%l)
    while int(r) not in range(1,l+1):
        r = raw_input("incorrect choice, please select a value between 1 and %s) : "%l)
    return listChoices[int(r)-1]
    

def showFinalQuestionsTUI(texts):
    questions = generateFinalQuestions(texts)
    
    instruction = "To finish, we wish to ask %s quick questions." %(len(questions))
    #print taskname
    print instruction

    try:
        input= raw_input("(Press any key to continue)")
    except NameError:
        pass

    responses = {}
        
    MW.dumpBuffer()
    os.system("tput cnorm")
    for i,q in enumerate(questions):
        os.system("clear && printf '\e[3J'")
        print "Question %s/%s" %(i+1,len(questions)) 
        
        
        
        
        if q['type'] == 'free_response':
            try:
                niceTextDisplay(q['question'])
                #print "(Press Enter to go to next question.)"
                rStart = time.time()
                r = raw_input()
                rEnd = time.time()
                print "\n\n"
            except NameError:
                pass


        if q['type'] == 'unique_choice':
            try:
                niceTextDisplay(q['question'])
                #print 'Enter a unique value (1 to %s) corresponding to your choice .'%len(q['choices']) 
                for i,c in enumerate(q['choices']):
                    print "%s. %s"%(i+1,c)
                #print "\n"
                rStart = time.time()
                r = raw_input("(Enter any value between 1 and %s) : "%len(q['choices']))
                while int(r) not in range(1,len(q['choices'])+1):
                    r = raw_input("incorrect choice, please select a value between 1 and %s) : "%len(q['choices']))
                    
                rEnd = time.time()
                print "\n\n"
            except NameError:
                pass


        if q['type'] == 'ordered_choice':
            try:
                niceTextDisplay(q['question'])
                for i,c in enumerate(q['choices']):
                    print "%s. %s"%(i+1,c)
                print "\n"
                rStart = time.time()
                r = raw_input("Enter comma separated numbers corresponding to articles (most comfortable / higher attention first): ")
                r = {'input': q['choices'],"choices" : r.split(",")}
                
                while sum(map(int,r['choices']))!=sum(range(1,i+2)):
                    print "Incorrect entry :-( Please try again: "
                    r = raw_input("Enter comma separated numbers corresponding to articles (most comfortable / higher attention first): ")
                    r = {'input': q['choices'],"choices" : r.split(",")}
                rEnd = time.time()
                print "\n\n"
            except NameError:
                pass

        responses[i+1] = {'t0': rStart, 't1' : rEnd, 'response' : r}
    
    eegData = MW.dumpBuffer()
    responses['eegData'] = eegData
    return responses


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
        self.entropy_window = 512
        self.deque = 10
        self.adaptivity = -0.005
        self.currentEntropy = 0
        self.entropy = [0]
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
        rawEEG = zip(*MW.raw_data[-self.entropy_window:])[2]
        
        try:
            if np.median(rawEEG) > 150:
                ''' If raw data exhibits large deviation, take the median of the entropy on the last 10 measures'''
                self.entropy.append(np.median(self.entropy[-10:]))
            else:
                #print rawEEG
                #print compute_entropy(rawEEG,1)
                self.entropy.append(compute_entropy(rawEEG,1))
            
            self.normalized_entropy.append(normalize(self.entropy[-self.deque:])[-1])                
            self.currentEntropy = self.normalized_entropy[-1]
        except:
            pass

    def updateRate(self,treatment):
        if treatment=="bsrPlus":
            try:
                self.getCurrentEntropy()
                self.currentRate = self.currentRate*(1 + (self.adaptivity*self.currentEntropy))
            except:
                pass
        
        elif treatment=="bsrMinus":
            try:
                self.getCurrentEntropy()
                self.currentRate = self.currentRate*(1 - (self.adaptivity*self.currentEntropy))
            except:
                pass
            
        elif treatment=="ar1":
            self.getCurrentEntropy()
            self.currentRate = self.AR1()
        
        elif treatment=="cst":
            self.getCurrentEntropy()
            self.currentRate = self.currentRate
        
        if self.currentRate > 175:
            '''introduce a lower speed broundary'''
            self.currentRate == 175
            
        if self.currentRate < 30:
            '''introduce a higher speed broundary'''
            self.currentRate == 30
            
        
        
    def RSVP(self,articleJson,treatment):
        
        taskname = "rsvp"
        instruction = '''You will see words displayed one at the time at some varying speed. 
        As much as you can, try to get the general meaning of the text and try to memorize 
        important key words, as well as important people, places, organizations and institutions.'''

        MW.dumpBuffer()
        time.sleep(3)
    
        #print taskname
        print "\n"
        print niceTextDisplay(instruction,lineSleep=0.2)
        print "\n"
        try:
            input= raw_input("(Press any key to continue)")
        except NameError:
            pass


        self.currentRate = self.initRate
        self.entropy = [0]
        self.normalized_entropy = [0]
        self.rate = [self.initRate]
        self.words = ['x']
        self.time = [time.time()]
        self.t0 = self.time[0]
        
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
        t = [ item - self.t0 for item in self.time]
        t = t[:]
        
        time.sleep(1)
        os.system("tput cnorm")
        responses = showQuestionsTUI(articleJson)
        os.system("tput civis")
        
        eegData = MW.getRawEEG()
        
        expDic  = {'eegData':eegData, 
                   "responses" : responses,
                   'exp': {'rate': self.rate,
                           'entropy' : self.entropy,
                           'normalized_entropy' : self.normalized_entropy,
                           'words' : self.words, 
                           'timestamps' : t,
                           't0': self.t0, 
                           'adaptivity' : self.adaptivity,
                           'entropy_window' : self.entropy_window,
                           'deque' : self.deque
                           }
                   }
               
        
        return expDic
    
        '''
        MW.raw_data = []
        time.sleep(5)
        J = self.showWords(articleJson,treatment)
        eegData = MW.getRawEEG()
        return {'exp' : J,'eegData' : eegData}
        '''
    
    def printWord(self,word):
        showWord(word)
        
        '''
        print "\n" * 10
        print "\t" *5, "%s"%(word)
        #print "\t  " *4, "(%.2f,%.0f)"%(self.currentEntropy,self.currentRate)
        print "\n" * 10
        '''
        
        #print "\n" * 5
        #print "\t" *3, "%s"%(word)
        #print "\t" *3, "(%.3f)"%(self.currentRate)
        #print "\n" * 5
    

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
    treatment = "bsrPlus"
    J= RSVP(aDic[1],treatment)
    return J



    
if __name__ == '__main__':
    print "blah"
    

    #J = runTest()
    

    
