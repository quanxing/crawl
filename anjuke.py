#coding=utf-8

from bs4 import BeautifulSoup
import time
import json
import sys
import requests
import traceback
import re
import sys
import numpy
import urllib
from pandas import Series, DataFrame
import pandas as pd

reload(sys)
sys.setdefaultencoding('utf8')


source_url='http://zz.fang.anjuke.com/loupan/all/'
headers={
        "User-Agent": 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:53.0) \
        Gecko/20100101 Firefox/53.0'}

pages = ['p1_w1/']

        
class Spiders(object):

    """get the house price  from anjuke"""

    #init
    def __init__(self):
        self.s = requests.session()
        self.infor = {}
        self.hname = [u'一室',u'二室',u'三室',u'四室',u'五室']

    def getResponse(self, url):
        try:
            response = self.s.get(url.strip(), headers=headers)
            soup = BeautifulSoup(response.text, 'lxml')
            return soup

        except Exception as e:
            print "EXCEPTIONURL ", url
            print 'EXCEPTION: ConnectionError: ', e
            sys.exit(1)


    """get detail info"""
    def get_firstpage_info(self, url):
        soup = self.getResponse(url.strip())
        #参考房价 <em class="sp-price">
        price_infor = soup.find_all('em',attrs={'class':'sp-price'})
        if len(price_infor) !=0 :
            self.infor['price'] = (price_infor[0]).get_text()
        else:
            self.infor['price'] = '待定'

        #完整的城区地址,这里是有个字符集的坑，需要整理一下
        full_address = (soup.find('span',attrs={'class':'lpAddr-text'})).get_text()
        regions =  re.findall(r'\[(.+?)\]',full_address)[0]
        regions =  regions.replace(u'\xa0',' ').strip().split(' ')[0]
        self.infor['region'] = regions

        #若网站格式统一的话
        address = full_address.replace(u'\xa0','').split()
        if len(address) > 1:
            self.infor['addr'] = address[-1]
            # print u'api查询地址',self.infor['addr']
        else:
            self.infor['addr'] = '未知'

        # baidu api  return 
        # {"status":0,"result":{"location":{"lng":113.66900038158664,"lat":34.865929851039158},"precise":0,"confidence":30,"level":"道路"}}
        addinfo = self.getGeo(self.infor['region'] + self.infor['addr'])
        # print u"地址", addinfo
        if 'result' in addinfo.keys():
            if 'location' in addinfo['result'].keys():
                if 'lng' in addinfo['result']['location'].keys():
                    self.infor['lng']  = addinfo['result']['location']['lng']
                if 'lat' in addinfo['result']['location'].keys():
                    self.infor['lat']  = addinfo['result']['location']['lat']

        #{户型:平均面积}
        #这个户型也需要在户型页面 找出每个户型的状态，面积
        self.infor['huxing'] = {}
        
        models = soup.find_all('a',attrs={'soj':'loupan_index_huxing'})  #soj="loupan_index_huxing"
        for model in models:
            model_url = model.get('href')
            model_avgArea = self.get_AvgArea(model_url)
            model_name = model.get_text()
            mname = re.findall(ur'[\u4e00-\u9fa5]+',model_name)[0]
            self.infor['huxing'][mname] = model_avgArea

        #为了csv格式统一，将没有户型面积设置为0
        extra_name = list(set(self.hname).difference(set(self.infor['huxing'].keys())))
        for key in extra_name:
            self.infor['huxing'][key] = 0

        #detailPage
        taga = soup.find_all('a')
        for tag in taga:
            href = tag.get('href')
            if href != None and  len(href) != 0  and 'canshu' in href:
                self.get_detail_page(href)


    def get_detail_page(self, url):
        # <a target="_blank" soj="canshu_left_kfs" href="/loupan/kfs-14572.html">郑州奥星实业有限公司</a>
        keys = ['开发商','开盘时间','交房时间','容积率','绿化率']
        soup = self.getResponse(url.strip())
        lis = soup.find_all('li')
        # tmp = lis[-1]
        # print tmp.find_all('span')
        for li in lis:
            div_name = li.find_all('div', attrs={'class':'name'})
            div_des = li.find_all('div', attrs={'class':'des'})
            if len(div_name) != 0 and len(div_des):
                if div_name[0].get_text() in keys:
                    if keys.index(div_name[0].get_text()) == 0:
                        kaifashang = div_des[0].find_all('a')
                        if len(kaifashang) != 0:
                            self.infor['kaifashang'] = kaifashang[0].get_text()
                        else:
                            self.infor['kaifashang'] = '未知'

                    else:
                        strr = str(div_des[0]).decode('utf8')
                        # pattern = '^\d{4}-\d{1,2}-\d{1,2}$'
                        if '开盘时间' in div_name[0].get_text():
                            stime = re.findall('\d{4}-\d{1,2}-\d{1,2}',strr)
                            if len(stime) != 0:
                                self.infor['startTime'] = stime[0]
                        else:
                            self.infor['startTime'] = '待定'
                            # print re.findall('\d{4}-\d{1,2}-\d{1,2}',strr)
                        if '交房时间' in div_name[0].get_text():
                            etime = re.findall('\d{4}-\d{1,2}-\d{1,2}',strr)
                            if len(etime) != 0:
                                self.infor['finishTime'] = etime[0]
                        else:
                            self.infor['finishTime'] = '待定'

                        if '容积率' in div_name[0].get_text():
                            rjl =  re.findall('\d+\.\d+',strr)
                            if len(rjl) != 0:
                                self.infor['rjl'] = rjl[0]
                        else:
                            self.infor['rjl'] = '待定'

                        if '绿化率' in div_name[0].get_text():
                            lvhua =  re.findall('\d+\.\d+',strr)
                            if len(lvhua) != 0:
                                self.infor['lvhua'] = lvhua[0]
                        else:
                            self.infor['lvhua'] = '待定'


    def get_AvgArea(self,url):
        soup = self.getResponse(url.strip())
        # <span class="desc-k area-k">建筑面积：约87.00m²</span>
        areas = soup.find_all('span',attrs={'class':'desc-k area-k'})
        sum = 0
        for i in range(len(areas)):
            #建筑面积：约87.00m²
            str = areas[i].get_text()
            value = re.findall(r'\d+.\d+',str)
            sum += float(value[0])
        return round(sum/len(areas),2)


    def getInfo(self):

        # for i in pages:
        #     url = source_url + i
        directurl = source_url + pages[0]
        flag = True
        while (flag):
            soup = self.getResponse(directurl)
            print "current page", directurl
            next_link = soup.find_all('a',attrs={'class':'next-page next-link'})
            if len(next_link) != 0:
                directurl = next_link[0].get('href')
                print "next page", directurl
            else:
                flag = False

            showInfo = soup.find_all('div',attrs={'class':'infos'})
            with open('showInfo.csv','a+') as f:
                for info in showInfo:
                    # 楼盘名称
                    self.infor['name'] = info.find('a', attrs={'class':'items-name'}).string
                    #firstpage
                    url = (info.find('a')).get('href') # 直接获取文本string
                    self.get_firstpage_info(url)

                    #status
                    status_icon = info.find_all('i') #<i class="status-icon onsale">
                    hstatus = ''
                    for icon in status_icon:
                        hstatus += icon.get_text() + " "
                    hstatus =  hstatus.strip().split(' ')
                    if len(hstatus) ==2:
                        hstatus = hstatus[1]
                    elif len(hstatus) ==  1:
                        hstatus = hstatus[0]
                    #只保留在售或者待售状态的的数据
                    if hstatus == '售罄':
                        flag = False
                        break

                    self.infor['status'] = hstatus
                    #['finishTime', 'status', 'huxing', 'name', 'region', 'lvhua', 'startTime', 'rjl','price','kaifashang']
                    result = ''
                    # print u'详情',self.infor['name']
                    result += self.infor['name'] + "," + self.infor['region'] + "," + \
                    self.infor['status'] + "," + self.infor['lvhua'] +"," +\
                    self.infor['rjl'] + "," + self.infor['price'] + ","

                    for i in range(len(self.hname)):
                        result += str(self.infor['huxing'][self.hname[i]])+","
                    result += self.infor['startTime'] + "," + self.infor['finishTime'] + "," + self.infor['kaifashang']
                    result += "," + str(self.infor['lng']) +"," + str(self.infor['lat'])
                    # print result
                    f.write(result +"\n")


    #给 文件 添加列名 showInfo.csv
    def titleFile(self):
        #此时还没有写入 通勤时间，通勤距离
        names = self.infor.keys()
        df = pd.read_csv('./showInfo.csv',sep=',',names=names)
        df.to_csv('./showInfo.csv',index=False)

    #获取楼盘坐标字典-热力图
    #http://developer.baidu.com/map/jsdemo.htm#c1_15
    def getGeo(self,addr):
        # print u"api查询的地址",addr
        url =  'http://api.map.baidu.com/geocoder/v2/?output=json&ak=j19RXQ4y9X0bckbcbD3DwVNuHy9ke042&address={addr}'
        url = url.format(addr=addr)
        response = self.s.get(url.strip(), headers=headers)
        tmp =  response.json()
        return tmp

    #获取公交路线及时间
    def getDistance(self):
        
        this_des = '34.81414339771011,113.54219685229028' #河南省郑州市金水区农业东路99号
        this_ak = 'j19RXQ4y9X0bckbcbD3DwVNuHy9ke042'
        
        tranTime = []
        tranDistancec = []
        tranName = []

        df = pd.read_csv('./showInfo.csv', sep=',')
        for i in df.index:
            lng = df.ix[i]['lng']
            lat = df.ix[i]['lat']
            this_origin = str(lat) + ',' + str(lng)
            #format url
            url = 'http://api.map.baidu.com/direction/v2/transit?origin={origin}&destination={des}&ak={ak}&tactics_incity=1'
            url = url.format(ak=this_ak,origin=this_origin,des=this_des)
            distanceDit = self.getDisTimeJson(url)

            tranTime.append(distanceDit['tranTime'])
            tranDistancec.append(distanceDit['tranDistancec']) 
            tranName.append(distanceDit['tranName'].rstrip(','))

        # print len(tranName)
        # print len(tranTime)
        # print len(tranDistancec)
        df['tranTime']  = tranTime
        df['tranDistancec'] = tranDistancec
        df['tranName'] = tranName

        df.to_csv('./showInfo.csv',index=False)

    def getDisTimeJson(self,url):
        response = self.s.get(url.strip(), headers=headers)
        # print response
        tmp =  response.json()
        distanceDit = {}
        # print url
        if tmp['status'] == 1001 or tmp['status'] == 1002 or len(tmp['result']['routes']) == 0:
            #未开通交通路线的
            print u'未开通'
            distanceDit['tranDistancec'] = '未知'
            distanceDit['tranTime'] = '未知'
            distanceDit['tranName'] = '未知,'
            # print len(tmp['result']['routes'])
            # print url
        else:
            distanceDit['tranDistancec'] = tmp['result']['routes'][0]['distance']
            distanceDit['tranTime'] = tmp['result']['routes'][0]['duration']
            distanceDit['tranName'] = ''

            for i in range(len(tmp['result']['routes'][0]['steps'])):
                if 'vehicle_info' in tmp['result']['routes'][0]['steps'][i][0].keys():
                    if tmp['result']['routes'][0]['steps'][i][0]['vehicle_info']['detail'] != None:
                        distanceDit['tranName'] += tmp['result']['routes'][0]['steps'][i][0]['vehicle_info']['detail']['name']+','
        return distanceDit

if __name__ == '__main__':
    spider = Spiders()
    #写数据
    spider.getInfo()
    #写列名
    spider.titleFile()
    #房价热力力图 ok
    #起码要用百度地图得出每个楼盘到目的地的最快公交，时间，路程ok
    spider.getDistance()
    

