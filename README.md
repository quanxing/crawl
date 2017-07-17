#爬取安居客房价
####为将来自己找房子提供便利


###程序架构

----------

- class Spiders
   - getInfo()
       - get_firstpage_info()
           - getGeo()
           - get_detail_page()
           - get_AvgArea()
    - getDistance()
        - getDisTimeJson()
    - titleFile()
    - main
        - getInfo()
        - titleFile()
        - getDistance()

###程序说明
----------

1. getInfo() 函数是爬取房价的核心函数

    1.  获取下一页楼盘的nextURL
    2.  并调用get_firstpage_info()
    
2. get_firstpage_info() 主要用来爬取当前页楼盘的各个基础属性信息，例如楼盘名称，价格，位置，户型等信息。它调用了get_detail_page()方法，getGeo()方法和get_AvgArea()方法

3. get_detail_page()方法主要用来得到 '开发商','开盘时间'等楼盘的信息，再调用了get_AvgArea()方法
4. get_AvgArea()主要计算具体楼盘每个户型的平均面积
5. getGeo()主要实现地址到百度坐标的转换
6. titleFile()方法实现为结果文件showInfo.csv添加列名
7. getDistance()借助getDisTimeJson()方法实现了 所有楼盘距离目的地的通勤距离，时间，公交路线信息

###TIPS
----------
###[http://lbsyun.baidu.com/index.php?title=webapi](http://lbsyun.baidu.com/index.php?title=webapi "百度地图api")

###Forward

----------

###准备拿到这些数据利用pandas进行简要分析，从单房价，总房价，区域位置，交通状况等信息综合挑选出合适的楼盘

