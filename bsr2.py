from readNeuroskyData import readMindwave
MW = readMindwave()
from tasks import *
bsr = bsr()
import uuid
import requests
from datetime import datetime
import threading


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
    r = requests.put('http://brainspeedr.s3.amazonaws.com/bsr/%s/%s/%s_%s.%s'%(now[:10],token,now[11:],task,extension), data=Json)


def configureExperiment():
    '''add preliminary tasks'''
    prelimTasks = [{'func' : blink5times, 'params' : ()},{'func' : restingState, 'params' : ()}, {'func' : doMath , 'params' : ()}, {'func' :readTextEnglish , 'params' : ()}]
    #random.shuffle(prelimTasks)
    experimentConfig = prelimTasks
    
    #experimentConfig = []
    
    '''pre-select articles'''
    articles = listArticles()
    articles = [articles[1],articles[2],articles[6],articles[4]]
    random.shuffle(articles)
    
    '''add treatment tasks'''
    treatments = ['ar1','cst','bsr+','bsr-']
    random.shuffle(treatments)
    
    for i in range(4):
        experimentConfig.append({'func' : bsr.RSVP, 'params' : (articles[i], treatments[i])})
    
    return experimentConfig


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


def runExperiment():
    
    token = str(uuid.uuid4())[-12:]

    
    J = {}
    
    start = time.time()
    now = time.time()

    tEEG = threading.Thread(target=MW.readRawEEG)
    tEEG.daemon = True
    tEEG.start()

    time.sleep(5)
    MW.connectionCheck()
    time.sleep(2)
    MW.qualityCheckLoop()


    config = configureExperiment()

    for i,f in enumerate(config):
        

        MW.qualityCheckLoop()
        
        #return f
        
        try:
            type = f['params'][1]
        except:
            type = ""
            
        print "task %s, %s, %s"%(i,f['func'],type)
        J[i] = f['func'](*f['params'])
        
        if f['func'].__name__ == 'RSVP':
            qJson = generateQuestions(f['params'][0]) 
            print qJson
      
        '''upload json'''
        task = "%02d_%s_%s"%(i,f['func'].__name__,type)
        uplodJson(J,token,task,compress=False)
        
        
    print "done"
    return J



if __name__ == '__main__':
    #print "blah"
    aDic = listArticles()
    articleJson = aDic[1]
    
    #bsr = bsr()
    J = runExperiment()
    #J = runTest()
    