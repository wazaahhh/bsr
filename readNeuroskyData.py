from mindwave_mobile import ThinkGearProtocol, ThinkGearRawWaveData, ThinkGearEEGPowerData, ThinkGearPoorSignalData, ThinkGearAttentionData, ThinkGearMeditationData
from datetime import datetime
import time
import threading
import random
import json
import os
import numpy



class readMindwave():
    def __init__(self):
        self.port = '/dev/tty.MindWaveMobile-DevA'
        self.signal_quality = 100
        self.eeg_data = 0  
        self.now = time.time()
        self.raw_data = []
    
            
    def readRawEEG(self):
        '''read and timestamp raw EEG signal from Neurosky Mindwave'''
        for pkt in ThinkGearProtocol(self.port).get_packets():
            self.now = time.time()
            for d in pkt:
                if isinstance(d, ThinkGearPoorSignalData):    
                    self.signal_quality = int(str(d))
                    #print "sigqual: ",self.now,self.signal_quality
                                
                if isinstance(d,ThinkGearRawWaveData):
                    self.eeg_data = int(str(d))
                    #print "raw: ",self.now,self.raw_data
    
            self.raw_data.append([self.now,self.signal_quality,self.eeg_data])
    
    
    def getRawEEG(self):
        '''Return a dictionary of raw signal, since last dump'''
        #return self.now,self.signal_quality,self.raw_data
        try:
            data = self.raw_data
            data = zip(*data)
            t = data[0]
            t0 = t[0]
            t = [ item - t0 for item in t]
            return {'t0' : t0,'t' : t, 'sigqual'  : data[1], 'rawsig' : data[2]}
        except:
            print "no data in buffer"

    def dumpBuffer(self):
        '''Return a dictionary of dump of raw signal. Raw signal is erased'''
        try:
            dic = self.getRawEEG()
            self.raw_data = []
            return dic
        except:
            return
     

    def connectionCheck(self,tests = 2,sleepTime = 4):
        '''Check connection by performing 5 consecutive dumps'''
        lRaw = 0
        for i in range(tests):
            time.sleep(sleepTime)
            raw = self.dumpBuffer()
            
            if len(raw['sigqual']) > 0:
                lRaw +=1
                print "check %s of %s : passed (%s)" %(i,tests,len(raw['sigqual'])) 
            else:
                print "check %s of %s : failed (%s)" %(i,tests,len(raw['sigqual']))
                 
        return lRaw
    
    def qualityCheck(self,duration = 10):
        '''Check average quality over a duration (in seconds) 
        on a scale from 0 to 100 (0 means good quality)'''
        
        try:
            raw = self.getRawEEG()
        except:
            print "no data in buffer"
            
        sigqual = raw['sigqual'][-duration*512:]
        
        mSigqual = numpy.mean(sigqual)
        return mSigqual
    
    def qualityCheckLoop(self):
        '''Performs quality check loop until quality is good (i.e., 0)'''
        
        sigqual = self.qualityCheck(duration = 2)
        while sigqual > 5:
            ''' check signal quality'''
            print "poor signal quality (%.2f), please replace headset."%sigqual
        
            try:
                input= raw_input("Press any key to continue")
            except NameError:
                pass
            
            sigqual = self.qualityCheck(duration = 2)
    
        print "signal quality : good"
    
    
    def runTest(self,duration):
        
        input = raw_input("Test Connection (y/n) : ")   
        if input=='y':
            output = self.tryConnection(verbose=True)
 
            if output < 1:
                return

        start = time.time()
        now = time.time()
    
        tEEG = threading.Thread(target=self.readRawEEG)
        tEEG.daemon = True
        tEEG.start()

        time.sleep(duration)
        return self.getRawEEG()   



    def run(self):
        
        self.tryConnection(verbose = False)
        
        J = {}
        
        start = time.time()
        now = time.time()
    
        tEEG = threading.Thread(target=self.readRawEEG)
        tEEG.daemon = True
        tEEG.start()

        time.sleep(5)

        fList = [blink5times,restingState,doMath,readTextEnglish]
        random.shuffle(fList)
        
        for i,f in enumerate(fList):    
            print "task %s"%i
            J[f.func_name] = f()
            
        print "done"
        return J


if __name__ == '__main__':
        
    MW = readMindwave()    
    #output = MW.run(10)
    #print output

    tEEG = threading.Thread(target=MW.readRawEEG)
    tEEG.daemon = True
    tEEG.start()
    time.sleep(5)
    
    MW.connectionCheck()
    time.sleep(2)
    MW.qualityCheckLoop()

    '''
    input = raw_input("Test Connection (y/n) : ")   
    if input=='y':
        output = tryConnection(verbose=True)

    if output < 1:
        pass
    else:
        start = time.time()
        now = time.time()
    
        tEEG = threading.Thread(target=MW.readRawEEG)
        tEEG.daemon = True
        tEEG.start()

        time.sleep(15)
#        while now < start + 30:
#            now = time.time()
        print MW.getRawEEG()
   
        #print start,now
'''
    
    
'''
    def tryConnection(self,verbose = False):
        #try connection and signal quality until 
        #it has gone to 0 for at least 5 seconds
        
        #print "checking connection with Mindwave brainscanner (takes a few seconds)."
        sigqual = [100]
        start = time.time()
        output = -1
        time.sleep(2)
        
        try:
            for pkt in ThinkGearProtocol(self.port).get_packets():
                for d in pkt:
                    if isinstance(d, ThinkGearPoorSignalData):
                        sigqual.append(int(str(d)))
                
                dt = time.time() - start
                
                if dt  > 15 and len(sigqual)==1:
                    if verbose:
                        print "no connection"
                    output = -1
                    break
                
                elif len(sigqual) > 5 and sum(sigqual[-5:]) == 0:
                    if verbose:
                        print "connection ok"
                    output = 1
                    break
                    
                elif dt > 15 and len(sigqual) > 12 :
                    if verbose:
                        print "poor quality"
                    output = 0
                    break
        except:
            if verbose:
                print "no connection"
            output = -1
        
        return output
    '''

        