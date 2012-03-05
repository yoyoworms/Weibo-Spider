#! /usr/bin/env python
#coding=utf-8

import urllib
import httplib2
import sqlite3
import string
from BeautifulSoup import BeautifulSoup
import re
import time
import socket

BASE_URL = 'http://weibo.cn'

# Task List
todoUidList = [ '1981015097',
                '1492318831',
                '1772816433',
                '1696568687',
                '1849620990',
                '1762278155',
                '1504917330',
                '1700790770',
                '1770430112',
                '1411677642',
                '1769938382',
                '2013847173',
                '1894162113',
                '1740481037',
                '1525396823',
                '1916515895',
                '1712835361',
                '1612716553',
                '2094351590',
                '1719088662'
                ]

# Sql parameter
conn = sqlite3.connect('E:\weibo.sqlite')
c = conn.cursor()

#Create table
c.execute('''create table user (uid text primary key, gender text, district text, tags text)''')
c.execute('''create table relation (id integer primary key autoincrement, following_uid text, follower_uid text)''')


socket.setdefaulttimeout(30)

# Http parameter
http = httplib2.Http()

headers = {
    'Host': 'weibo.cn',
    'Connection': 'keep-alive',
    'User-Agent': 'Mozilla/5.0 (iPhone; U; CPU OS 4_2_1 like Mac OS X) AppleWebKit/532.9 (KHTML, like Gecko) Version/5.0.3 Mobile/8B5097d Safari/6531.22.7',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Encoding': 'gzip, deflate',
    'Accept-Language': 'zh-cn,zh;q=0.5',
    'Refer': 'http://weibo.cn/',
    'Cookie': 'gsid_CTandWM=3_58a34dc67f0151cb05ea47014a107722eff682; _T_WL=1; _WEIBO_UID=1639015412',
    }


#get the Tags from user's url 
def getTags(uid):
    tagUrl = BASE_URL + '/account/privacy/tags/?uid=' + uid
    soup = soupfy(tagUrl)
    
    tags = soup.findAll('a', attrs={'href': re.compile(u"^/search"), 'class':None})
    
    tagList = []
    for tag in tags:
        tagList.append(tag.text)
    return ','.join(tagList)


#
def getInfos(uid):
    infoUrl = BASE_URL + '/' + uid + '/info'
    soup = soupfy(infoUrl)

    districBlock = soup.find('br', text=re.compile(u"地区"))
    genderBlock = soup.find('br', text=re.compile(u"性别")) 
    if districBlock == None or genderBlock == None:
        return False
    
    distric = districBlock[3:]   
    gender = genderBlock[3:]
    
    tags = getTags(uid)
    
    c.execute("""insert into user(uid, gender, district, tags)
            values(?, ?, ?, ?)""",(uid, gender, distric, tags))  
    conn.commit()
    return True  
    

##get the uid from user's url 
#def getUid(userUrl):
#    userUrl = BASE_URL + userUrl
#    response, content = http.request(userUrl, 'GET', headers=headers)
#    soup = BeautifulSoup(content)
#    
#    
#    uidBlock = soup.find('a', text = re.compile(u"^资料"))
#    uid = uidBlock.parent['href']
#    uid = uid[1:-5]
#    
#    return uid
    
    

#return a list of one's following users' url
def getFollowing(uid):
    followingUrl = BASE_URL + '/' + uid + '/follow'
    soup = soupfy(followingUrl)

    pageNum = soup.find('input',attrs={'name': 'mp'})
    if pageNum == None:
        maxPageNum = '1'
    else:
        maxPageNum = pageNum['value']
    
    followingNumBlock = soup.find('span', attrs={'class': 'tc'})
    if followingNumBlock == None:
        return False
    
    followingNum = followingNumBlock.string
    begin = followingNum.find('[')
    end = followingNum.find(']')
    followingNum = followingNum[begin+1:end]
    
    if string.atoi(followingNum) > 500:
        return False
    

    for i in range(1, string.atoi(maxPageNum)+1):
        url = BASE_URL + '/' + uid + '/follow?page=' + str(i)
        soup = soupfy(url)
        
        allImgs = soup.findAll('img', alt='pic', src=re.compile(u"sinaimg"))
        
        for img in allImgs:
            src = img['src']
            begin = src.find('cn/')
            end = src.find('/50')
            followingUid = src[begin+3:end]
            
            c.execute("""insert into relation(following_uid,follower_uid)
                    values(?, ?)""",(followingUid,uid))  
            conn.commit()
            # If set size is over 30000, do not add any user
            if len(todoUidList) < 30000:
                # If user already exists, do not add 
                if not (followingUid in todoUidList):
                    todoUidList.append(followingUid)
    
    return True



# Prevent socket error
def soupfy(url):
    while True:
        try:
            response, content = http.request(url, 'GET', headers=headers)
            soup = BeautifulSoup(content)
            
            return soup
        except:
            print "A socket error at " + time.strftime('%d-%H:%M',time.localtime(time.time()))  
            time.sleep(30)
            continue
            
        

def main():
    count = 0
    # Two pointer for todoUidList, one is count, the other is len, they are competing
    while count < len(todoUidList):
        uid = todoUidList[count]
        print uid
        print count
        print len(todoUidList)  
        print time.strftime('%d-%H:%M',time.localtime(time.time()))     
        if getInfos(uid):
            if not getFollowing(uid):
                c.execute('delete from user where uid=' + uid)  
                conn.commit()
        
        count = count + 1
        
    

if __name__ == '__main__':
    main()
