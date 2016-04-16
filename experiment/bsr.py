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
         'pressFreedomUS',
         ]


def uplodJson(Json,token,task,compress=False):
    if compress:
        extension="json.zlib"
        Json = zlib.compress(json.dumps(Json))
    else:
        extension="json"
        Json = json.dumps(Json)
       
    #key = bucket.new_key("/bsr/%s/%s/%s.json%s"%(get_mac(),textId,now,extension))
    #key.set_contents_from_string()
    r = requests.put('http://brainspeedr.s3.amazonaws.com/bsr/v%s/%s/%s.%s?x-amz-acl=bucket-owner-full-control'%(experiment_version,token,task,extension), data=Json)


def configureExperiment(lenExp):
    '''add preliminary tasks'''
    prelimTasks = [{'func' : blink5times, 'params' : ()},{'func' : restingStateOpenEyes, 'params' : ()}, {'func' : restingStateClosedEyes, 'params' : ()}, {'func' : doMath , 'params' : ()}, {'func' :readTextEnglish , 'params' : ()}]
    #random.shuffle(prelimTasks)
    experimentConfig = prelimTasks
    #experimentConfig = []

    '''add treatment tasks'''
    treatments = ['bsrPlus','bsrMinus','cst','bsrPlus','bsrMinus']
    #treatments = ['bsrMinus']
    treatments = treatments[:lenExp-1]
    random.shuffle(treatments)
    treatments = ['cst'] + treatments
    
    '''pre-select articles'''
   
    aDic = getArticlesFromS3()
    articles = aDic.keys()
    random.shuffle(articles)
    articles = articles[:len(treatments)]

    saveConfig = {"treatments" : treatments ,"articles" : articles}
    
    for i in range(len(treatments)):
        experimentConfig.append({'func' : bsr.RSVP, 'params' : (aDic[articles[i]], treatments[i])})
    
    return experimentConfig,articles,saveConfig


def runExperiment(lenExp=3):
    token = str(uuid.uuid4())[-5:]
    
    os.system("clear && printf '\e[3J'")
    printIntroInstructions()
    os.system("clear && printf '\e[3J'")
    
    print "Your experiment token is: %s"%token
    print "Checking connection and signal quality. Please wait..."
    
    start = time.time()
    now = time.time()

    tEEG = threading.Thread(target=MW.readRawEEG)
    tEEG.daemon = True
    tEEG.start()

    time.sleep(4)
    MW.connectionCheck()
    time.sleep(2)
    MW.qualityCheckLoop()

    config,texts,saveConfig = configureExperiment(lenExp)
    uplodJson(saveConfig,token,"config",compress=True)

    k=1
    os.system("tput civis")
    for i,f in enumerate(config):
        os.system("clear && printf '\e[3J'")
        print "task %s/%s" %(i+1,len(config))
        MW.qualityCheckLoop()
        
                
        try:
            type = "_"+f['params'][1]
            if k==1:
                printRSVPinstructions()
                os.system("clear && printf '\e[3J'")
                k=0
        except:
            type = ""
        
        #print "task %s, %s, %s"%(i,f['func'],type)
        J = f['func'](*f['params'])
        
        if J.has_key('reponses'):
            J['meta'] = {'articleKey' : texts[i], 'uploadTime' : datetime.utcnow().strftime("%Y_%m_%d/%H%M%S"),'mac_address' : get_mac()}
        
        #Jfinal[i] = J


        '''upload json'''
        #print "please wait while data are uploaded"
        task = "%02d_%s%s"%(i,f['func'].__name__,type)
        uplodJson(J,token,task,compress=True)
        os.system("clear && printf '\e[3J'")
        
    os.system("clear && printf '\e[3J'")
    finalQ = showFinalQuestionsTUI(texts)
    #Jfinal[i+1]
    uplodJson(finalQ,token,"finalQ",compress=True)
    
    niceTextDisplay('''You successfully went through the Brain Speed Reader Experiment. Your experiment token is:  
    %s. Please write it down if you want to get access to the results of this experiment in the future. 
    Thank you for your time.'''%token)
    time.sleep(1.5)
    print "\n"
    os.system("tput cnorm")
    #return Jfinal


def runExperiment2(preliminaryTasks=True,randomTreatment=True, finalQuestions=True):
    
    token = str(uuid.uuid4())[-5:]
    i=0
    Jfinal = {}
    
    niceTextDisplay('''The brain speed reader experiment is about to start. 
                Please make sure that you have paired the Neurosky Mindwave on your computer: 
                (i) go in the bluetooth menu,
                (ii) select "Set up bluetooth device", 
                (iii) select 'press on/pair button on the headset),
                (iv) when the mindwave appears, click "add" and finish.
                (v) Place the headset on your head, with the sensors on your left forehead.''',lineSleep=0.5)
    input= raw_input("(Press Enter to continue)")

    
    start = time.time()
    now = time.time()

    tEEG = threading.Thread(target=MW.readRawEEG)
    tEEG.daemon = True
    tEEG.start()


    time.sleep(4)
    MW.connectionCheck()
    time.sleep(2)
    MW.qualityCheckLoop()
    
    print token
    os.system("tput civis")
    
    if preliminaryTasks:
        '''add preliminary tasks'''
        prelimTasks = [{'func' : blink5times, 'params' : ()},{'func' : restingStateOpenEyes, 'params' : ()}, {'func' : restingStateClosedEyes, 'params' : ()}, {'func' : doMath , 'params' : ()}, {'func' :readTextEnglish , 'params' : ()}]
        
        for i,f in enumerate(prelimTasks):
            os.system("clear && printf '\e[3J'")
            print "preliminary task %s/%s" %(i+1,len(prelimTasks))
            MW.qualityCheckLoop()
            
            #try:
            #    type = "_"+f['params'][1]
            #except:
            type = ""
                
            J = f['func'](*f['params'])
            Jfinal[i] = J   
            '''upload json'''
            #print "please wait while data are uploaded"
            task = "%02d_%s%s"%(i,f['func'].__name__,type)
            uplodJson(J,token,task,compress=True)
            os.system("clear && printf '\e[3J'")
        
    more = True
    texts = []
    
    printRSVPinstructions()
    
    while more:
        i+=1
        if len(articles)==0:
            more = False
        

        
        input= raw_input("(Press Enter to continue)")
        os.system("clear && printf '\e[3J'")
        
        choice = showArticleList(articles)
        texts.append(choice)
        articles.remove(choice)


        if randomTreatment:
            random.shuffle(treatments)
            treatment = treatments[0]
        else:
            print "Select the brainspeedreader treatment of your choice: "
            treatment = multipleChoiceQuestion(treatments)
        
        os.system("clear && printf '\e[3J'")    
        f = {'func' : bsr.RSVP, 'params' : (aDic[choice], treatment)}
        type = "_" + f['params'][1]
        #print "task %s, %s"%(f['func'],type)
        J = f['func'](*f['params'])
        Jfinal[i] = J
        
        J['meta'] = {'articleKey' : choice, 'uploadTime' : datetime.utcnow().strftime("%Y_%m_%d/%H%M%S"),'mac_address' : get_mac()}  
        
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
        else:
            more = False
    
    if finalQuestions:
        os.system("clear && printf '\e[3J'")
        i+=1
        finalQ = showFinalQuestionsTUI(texts)
        task = "%02d_%s"%(i,"finalQ")
        uplodJson(finalQ,token,task,compress=True)
     
        
    niceTextDisplay('''You successfully went through the Brain Speed Reader Experiment. Your experiment token is:  
    %s. Please write it down if you want to get access to the results of this experiment in the future. 
    Thank you for your time.'''%token)
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
    aDic = getArticlesFromS3()
    #print aDic.keys()
    
    treatment = "bsr+"
    J= bsr.RSVP(aDic['Ohmconnect'],treatment)
    #J= bsr.RSVP(aDic[1],treatment)
    return J


if __name__ == '__main__':
    
    global experiment_version
    experiment_version = 1.0
    
    global treatments
    treatments = ['cst','bsrPlus','bsrMinus']
    
    #runTest()
    #J = runExperiment(lenExp=4)
    #runExperiment2(preliminaryTasks=False,randomTreatment=True, finalQuestions=False)
    