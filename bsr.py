from readNeuroskyData import readMindwave
MW = readMindwave()
from tasks import *
bsr = bsr()
import uuid
from uuid import getnode as get_mac
import requests
from datetime import datetime
import threading
import os
import zlib

global articles
articles = ['bigPolluter',
         'emojiShortened',
         'indianFood',
         'marsOneShortened',
         'Ohmconnect',
         'pressFreedomUS']


def uplodJson(Json,token,task,compress=False):
    if compress:
        extension="json.zlib"
        Json = zlib.compress(json.dumps(Json))
    else:
        extension="json"
        Json = json.dumps(Json)
    
    now = datetime.utcnow().strftime("%Y_%m_%d/%H%M%S")
    #key = bucket.new_key("/bsr/%s/%s/%s.json%s"%(get_mac(),textId,now,extension))
    #key.set_contents_from_string()
    r = requests.put('http://brainspeedr.s3.amazonaws.com/bsr/v%s/%s/%s/%s/%s_%s.%s'%(experiment_version,now[:10],get_mac(),token,now[11:],task,extension), data=Json)


def configureExperiment():
    '''add preliminary tasks'''
    prelimTasks = [{'func' : blink5times, 'params' : ()},{'func' : restingStateOpenEyes, 'params' : ()}, {'func' : restingStateClosedEyes, 'params' : ()}, {'func' : doMath , 'params' : ()}, {'func' :readTextEnglish , 'params' : ()}]
    #random.shuffle(prelimTasks)
    experimentConfig = prelimTasks
    
    #experimentConfig = []
    
    '''pre-select articles'''
   
    aDic = getArticlesFromS3()
    articles = [aDic['indianFood'],aDic['bigPolluter'],aDic['pressFreedomUS']]
    random.shuffle(articles)
    
    '''add treatment tasks'''
    #treatments = ['ar1','cst','bsr+','bsr-']
    #treatments = ['cst','bsrPlus','bsrMinus']

    random.shuffle(treatments)
    
    for i in range(len(treatments)):
        experimentConfig.append({'func' : bsr.RSVP, 'params' : (articles[i], treatments[i])})
    
    experimentConfig.append({'func' : showFinalQuestionsTUI, 'params':()})
    
    return experimentConfig


def runExperiment():
    
    token = str(uuid.uuid4())[-12:]

    
    J = {}
    
    start = time.time()
    now = time.time()

    tEEG = threading.Thread(target=MW.readRawEEG)
    tEEG.daemon = True
    tEEG.start()

    time.sleep(4)
    MW.connectionCheck()
    time.sleep(2)
    MW.qualityCheckLoop()


    config = configureExperiment()

    os.system("tput civis")

    for i,f in enumerate(config):
      
        os.system("clear && printf '\e[3J'")
        print "task %s/%s" %(i+1,len(config))
        MW.qualityCheckLoop()
        
                
        try:
            type = "_"+f['params'][1]
        except:
            type = ""
            
        #print "task %s, %s, %s"%(i,f['func'],type)
        J[i] = f['func'](*f['params'])
        

        '''upload json'''
        #print "please wait while data are uploaded"
        task = "%02d_%s%s"%(i,f['func'].__name__,type)
        uplodJson(J,token,task,compress=True)
        os.system("clear && printf '\e[3J'")
        
        
    niceTextDisplay("You successfully went through the Brain Speed Reader Experiment. Thank you for your time.")
    time.sleep(1.5)
    os.system("tput cnorm")
    return J


def runExperiment2(preliminaryTasks=True):
    
    
    token = str(uuid.uuid4())[-12:]

    i=0
    J = {}
    
    start = time.time()
    now = time.time()

    tEEG = threading.Thread(target=MW.readRawEEG)
    tEEG.daemon = True
    tEEG.start()

    time.sleep(4)
    MW.connectionCheck()
    time.sleep(2)
    MW.qualityCheckLoop()
    
    os.system("tput civis")
    
    if preliminaryTasks:
        '''add preliminary tasks'''
        prelimTasks = [{'func' : blink5times, 'params' : ()},{'func' : restingStateOpenEyes, 'params' : ()}, {'func' : restingStateClosedEyes, 'params' : ()}, {'func' : doMath , 'params' : ()}, {'func' :readTextEnglish , 'params' : ()}]
        
        for i,f in enumerate(config):
            os.system("clear && printf '\e[3J'")
            print "preliminary task %s" %(i+1,len(prelimTasks))
            MW.qualityCheckLoop()
            
            #try:
            #    type = "_"+f['params'][1]
            #except:
            type = ""
                
            J[i] = f['func'](*f['params'])
                
            '''upload json'''
            #print "please wait while data are uploaded"
            task = "%02d_%s%s"%(i,f['func'].__name__,type)
            uplodJson(J,token,task,compress=True)
            os.system("clear && printf '\e[3J'")
        
    more = True
        
    while more:
        i+=1
        if len(articles)==0:
            more = False
            
        choice = showArticleList(articles)
        articles.remove(choice)

        
        random.shuffle(treatments)
        f = {'func' : bsr.RSVP, 'params' : (aDic[choice], treatments[0])}
        type = "_"+f['params'][1]
        print "task %s, %s"%(f['func'],type)
        J[i] = f['func'](*f['params'])
        
        '''upload json'''
        #print "please wait while data are uploaded"
        task = "%02d_%s%s"%(i,f['func'].__name__,type)
        uplodJson(J,token,task,compress=True)
        os.system("clear && printf '\e[3J'")
  
      
        if len(articles)>0:
            try:
                input= raw_input("Would you like to read another text? (y/n): ")
                if input=="y":
                    pass
                else:
                    more = False
            except NameError:
                pass

    
    

        
        
    niceTextDisplay("You successfully went through the Brain Speed Reader Experiment. Thank you for your time.")
    time.sleep(1.5)
    os.system("tput cnorm")
    return J
    
    

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
    J= bsr.RSVP(aDic[1],treatment)
    #J= bsr.RSVP(aDic[1],treatment)
    return J


if __name__ == '__main__':
    #print "blah"
 
    
    global experiment_version
    experiment_version = 1.0
    
    global treatments
    treatments = ['cst','bsrPlus','bsrMinus']
    
    global aDic
    aDic = getArticlesFromS3()
    
    
    
#     global articles
#     articles = ['bigPolluter',
#              'emojiShortened',
#              'indianFood',
#              'marsOneShortened',
#              'Ohmconnect',
#              'pressFreedomUS']
    
    #config = configureExperiment()
    
    #J = runExperiment()
    J = runExperiment2(preliminaryTasks=False)
    