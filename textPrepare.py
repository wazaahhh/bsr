from bs4 import BeautifulSoup
from urllib2 import Request,urlopen
from numpy import array,unique,arange,random
from readability.readability import Document
import re
from stemming.porter2 import stem

global cwords
cw = open("cwords2",'r')
cwords = cw.read()
cwords = cwords.split()

url = "http://www.technologyreview.com/news/532826/material-cools-buildings-by-sending-heat-into-space/"

def retrieveHtml(url):
    '''open url and retrieve html'''
    headers = { 'User-Agent' : 'Mozilla/5.0' }
    req = Request(url, None, headers)
    html = urlopen(req).read()
    
    return html

def cleanHtmlToText(html):
    '''clean html and return list of words to make it brainspeed readable'''
    title = Document(html).short_title()
    html = Document(html).summary()
    soup = BeautifulSoup(html)
    
    for script in soup(["script", "style"]):
        script.extract()    # rip it out
    
    text = soup.get_text()
    
    dicText = {'text': text , 'title' : title}
    
    return dicText
    
def prepareText(dicText):
    text = dicText['text']
    wordListRead = text.split()
    text = re.sub("[,.']"," ",text)
    text = text.lower()
        
    wordList = [x for x in wordListRead if x.isalpha()]
    
    try:
        title = dicText['title']
    except:
        title = " ".join(wordList[:10])
    
    return {'wordList' : wordList , 'title' : title,'wordListRead' : wordListRead}


def removeCwords(wordList):
    '''remove common words'''
    return [x for x in wordList if x not in cwords]


def selectWords(wordList,n,countBoundaries=[0,5],lenBoundaries=[5,100]):
    '''select words for recall questions with two possible right answers: 
    (i) exact word
    (ii) root word (e.g., radiates => radiat)
    '''
    
    uniq = unique(wordList)
    count = array([wordList.count(x) for x in uniq])
    countDic = dict(zip(*[uniq,count]))
    
    stemWdl = [stem(w) for w in wordList]
    uStemWdl = [stem(w) for w in uniq]
    
    countStemWdl = [stemWdl.count(x) for x in uStemWdl]

    uStemDic = dict(zip(*[uniq,uStemWdl]))    
    stemCountDic = dict(zip(*[uStemWdl,countStemWdl]))
    
    lengths = array([len(i) for i in uniq])
    cCount = (count >= countBoundaries[0])*(count <= countBoundaries[1])
    cLengths = (lengths >= lenBoundaries[0])*(lengths <= lenBoundaries[1])
    uWord = uniq[cCount*cLengths]
    count = count[cCount*cLengths]
    index = arange(len(uWord))
    random.shuffle(index)
    index = index[:n]
    
    uCountStem = []
    
    dic = {}
    for i in index:
        uw = uWord[i]
        #print i,uw,count[i],uStemDic[uw],stemCountDic[uStemDic[uw]]
        dic[uw] = list([count[i].item(),stemCountDic[uStemDic[uw]]])
        
        uCountStem.append(stemCountDic[uStemDic[uw]])
        
    #return uWord[index],count[index],uCountStem
    return dic



