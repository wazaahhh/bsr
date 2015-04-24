import os
import json
from nltk.tokenize import word_tokenize
from nltk.tag import pos_tag
from nltk import FreqDist
import numpy as np

def listArticles(folder):
    aDic = {}
    listA = os.listdir("articles/%s"%folder)
    
    if '.DS_Store' in listA: listA.remove('.DS_Store')
            
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


def findCommonNouns(articleJson,minFreq=2):
    #dicTypeWords = {"propernouns":'NNP','nouns':'NN'}
    tagged_sent = pos_tag(word_tokenize(articleJson['content']))
    
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
    aDic = listArticles(folder)
    list = []
    for articleJson in aDic.values():
        print articleJson['title']
        l = findCommonNouns(articleJson,minFreq=minFreq)
        list += l
    
    
    #list = np.array(zip(*list))
    #l2 = np.array(map(int,list[1]))
    #o = np.argsort(l2)[::-1]    
    #list = np.array(zip(*list))[o]
    
    if storeFile:
        output=open("wordlists/common_words",'wb')
        output.write("\n".join(np.unique(list)))
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







# def retrieveHtml(url):
#     '''open url and retrieve html'''
#     headers = { 'User-Agent' : 'Mozilla/5.0' }
#     req = Request(url, None, headers)
#     html = urlopen(req).read()
#     
#     return html
# 
# def cleanHtmlToText(html):
#     '''clean html and return list of words to make it brainspeed readable'''
#     title = Document(html).short_title()
#     html = Document(html).summary()
#     soup = BeautifulSoup(html)
#     
#     for script in soup(["script", "style"]):
#         script.extract()    # rip it out
#     
#     text = soup.get_text()
#     
#     dicText = {'text': text , 'title' : title}
#     
#     return dicText
#     
# def prepareText(dicText):
#     text = dicText['text']
#     wordListRead = text.split()
#     text = re.sub("[,.']"," ",text)
#     text = text.lower()
#         
#     wordList = [x for x in wordListRead if x.isalpha()]
#     
#     try:
#         title = dicText['title']
#     except:
#         title = " ".join(wordList[:10])
#     
#     return {'wordList' : wordList , 'title' : title,'wordListRead' : wordListRead}
# 
# 
# def removeCwords(wordList):
#     '''remove common words'''
#     return [x for x in wordList if x not in cwords]
# 
# 
# def selectWords(wordList,n,countBoundaries=[0,5],lenBoundaries=[5,100]):
#     '''select words for recall questions with two possible right answers: 
#     (i) exact word
#     (ii) root word (e.g., radiates => radiat)
#     '''
#     
#     uniq = unique(wordList)
#     count = array([wordList.count(x) for x in uniq])
#     countDic = dict(zip(*[uniq,count]))
#     
#     stemWdl = [stem(w) for w in wordList]
#     uStemWdl = [stem(w) for w in uniq]
#     
#     countStemWdl = [stemWdl.count(x) for x in uStemWdl]
# 
#     uStemDic = dict(zip(*[uniq,uStemWdl]))    
#     stemCountDic = dict(zip(*[uStemWdl,countStemWdl]))
#     
#     lengths = array([len(i) for i in uniq])
#     cCount = (count >= countBoundaries[0])*(count <= countBoundaries[1])
#     cLengths = (lengths >= lenBoundaries[0])*(lengths <= lenBoundaries[1])
#     uWord = uniq[cCount*cLengths]
#     count = count[cCount*cLengths]
#     index = arange(len(uWord))
#     random.shuffle(index)
#     index = index[:n]
#     
#     uCountStem = []
#     
#     dic = {}
#     for i in index:
#         uw = uWord[i]
#         #print i,uw,count[i],uStemDic[uw],stemCountDic[uStemDic[uw]]
#         dic[uw] = list([count[i].item(),stemCountDic[uStemDic[uw]]])
#         
#         uCountStem.append(stemCountDic[uStemDic[uw]])
#         
#     #return uWord[index],count[index],uCountStem
#     return dic



