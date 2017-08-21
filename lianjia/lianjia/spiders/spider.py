from scrapy import Spider,Request
import re
from lxml import etree
import json
from urllib.parse import quote
from lianjia.items import LianjiaItem


class Lianjia_spider(Spider):
    name = 'lianjia'
    allowed_domains = ['nj.lianjia.com']
    regions = {'gulou':'鼓楼',
               'jianye':'建邺',
               'qinhuai':'秦淮',
               'xuanwu':'玄武',
               'yuhuatai':'雨花台',
               'qixia':'栖霞',
               'jiangning':'江宁',
               'liuhe':'六合',
               'pukou':'浦口',
               'lishui':'涟水',
               'gaochun':'高淳'
    }

    def start_requests(self):
        for region in list(self.regions.keys()):
            url = "https://nj.lianjia.com/xiaoqu/" + region + "/"
            yield Request(url=url, callback=self.parse, meta={'region':region}) #用来获取页码

    def parse(self, response):
        region = response.meta['region']
        selector = etree.HTML(response.text)
        sel = selector.xpath("//div[@class='page-box house-lst-page-box']/@page-data")[0]  
        sel = json.loads(sel)  # 转化为字典
        total_pages = sel.get("totalPage")

        for i in range(int(total_pages)):
            url_page = "https://nj.lianjia.com/xiaoqu/{}/pg{}/".format(region, str(i + 1))
            yield Request(url=url_page, callback=self.parse_xiaoqu, meta={'region':region})

    def parse_xiaoqu(self,response):
        selector = etree.HTML(response.text)
        xiaoqu_list = selector.xpath('//ul[@class="listContent"]//li//div[@class="title"]/a/text()')
        for xq_name in xiaoqu_list:
            url = "https://nj.lianjia.com/chengjiao/rs" + quote(xq_name) + "/"
            yield Request(url=url, callback=self.parse_chengjiao, meta={'xq_name':xq_name, 'region':response.meta['region']})

    def parse_chengjiao(self,response):
        xq_name = response.meta['xq_name']
        selector = etree.HTML(response.text)
        content = selector.xpath("//div[@class='page-box house-lst-page-box']")  #有可能为空
        total_pages = 0
        if len(content):
            page_data = json.loads(content[0].xpath('./@page-data')[0])
            total_pages = page_data.get("totalPage")  # 获取总的页面数量
        for i in range(int(total_pages)):
            url_page = "https://nj.lianjia.com/chengjiao/pg{}rs{}/".format(str(i+1), quote(xq_name))
            yield Request(url=url_page, callback=self.parse_content, meta={'region': response.meta['region']})

    def parse_content(self,response):
        selector = etree.HTML(response.text)
        cj_list = selector.xpath("//ul[@class='listContent']/li")


        for cj in cj_list:
            item = LianjiaItem()
            item['region'] = self.regions.get(response.meta['region'])
            href = cj.xpath('./a/@href')  
            if not len(href):
                continue
            item['href'] = href[0]

            content = cj.xpath('.//div[@class="title"]/a/text()')  
            if len(content):
                content = content[0].split()  # 按照空格分割成一个列表
                item['name'] = content[0]
                item['style'] = content[1]
                item['area'] = content[2]

            content = cj.xpath('.//div[@class="houseInfo"]/text()')
            if len(content):
                content = content[0].split('|')
                item['orientation'] = content[0]
                item['decoration'] = content[1]
                if len(content) == 3:
                    item['elevator'] = content[2]
                else:
                    item['elevator'] = '无'

            content = cj.xpath('.//div[@class="positionInfo"]/text()')
            if len(content):
                content = content[0].split()
                item['floor'] = content[0]
                if len(content) == 2:
                    item['build_year'] = content[1]
                else:
                    item['build_year'] = '无'

            content = cj.xpath('.//div[@class="dealDate"]/text()')
            if len(content):
                item['sign_time'] = content[0]

            content = cj.xpath('.//div[@class="totalPrice"]/span/text()')
            if len(content):
                item['total_price'] = content[0]

            content = cj.xpath('.//div[@class="unitPrice"]/span/text()')
            if len(content):
                item['unit_price'] = content[0]

            content = cj.xpath('.//span[@class="dealHouseTxt"]/span/text()')  # 返回的是一个字符串列表
            if len(content):
                for i in content:
                    if i.find("房屋满") != -1:  # 找到了返回的是非-1得数，找不到的返回的是-1
                        item['fangchan_class'] = i
                    elif i.find("号线") != -1:
                        item['subway'] = i
                    elif i.find("学") != -1:
                        item['school'] = i
            yield item















































