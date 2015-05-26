import boto
import zlib
import json
import re

bucketName = "brainspeedr"
s3 = boto.connect_s3()
global bucket
bucket = s3.get_bucket(bucketName)


def retrieveExperiment(token):
    list = bucket.list("bsr/v1.0/%s"%token)
    expJson = {}
    listDic = {}
    for i,l in enumerate(list):
        #print re.findall("%s/(.*?)\."%token,l.name)[0]
        id = re.findall("%s/(.*?)\."%token,l.name)[0]
        listDic[i] = id
        expJson[id] = json.loads(zlib.decompress(l.get_contents_as_string()))
    return expJson,listDic



#key = bucket.get_key("bsr/v1.0/40dd6/01_RSVP_bsrPlus.json.zlib")
#zData = key.get_contents_as_string()
#J = json.loads(zlib.decompress(zData))


if __name__ == '__main__':
    token = "220aa"
    expJson,listDic = retrieveExperiment(token)
    