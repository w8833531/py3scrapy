# -*- coding: utf-8 -*-
import json
import re
import time, datetime
import scrapy
from scrapy.loader import ItemLoader
from py3scrapy.items import ZhihuQuestionItem, ZhihuAnswerItem



try:
    import urlparse as parse
except:
    from urllib import parse

try:
    from PIL import Image
except:
    pass
#sys.stdout = io.TextIOWrapper(sys.stdout.buffer,encoding='utf8')

class ZhihuSpider(scrapy.Spider):
    name = 'zhihu'
    allowed_domains = ['www.zhihu.com']
    start_urls = ['http://www.zhihu.com/']
    # 问题回答的URL
    start_answer_url = "https://www.zhihu.com/api/v4/questions/{0}/answers?sort_by=default&include=data%5B%2A%5D.is_normal%2Cis_collapsed%2Cannotation_action%2Cannotation_detail%2Ccollapse_reason%2Cis_sticky%2Ccollapsed_by%2Csuggest_edit%2Ccomment_count%2Ccan_comment%2Ccontent%2Ceditable_content%2Cvoteup_count%2Creshipment_settings%2Ccomment_permission%2Cmark_infos%2Ccreated_time%2Cupdated_time%2Creview_info%2Crelationship.is_authorized%2Cis_author%2Cvoting%2Cis_thanked%2Cis_nothelp%2Cupvoted_followees%3Bdata%5B%2A%5D.author.follower_count%2Cbadge%5B%3F%28type%3Dbest_answerer%29%5D.topics&limit={1}&offset={2}&sort_by=default"
    agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.115 Safari/537.36"
    headers = {
        "Host": "www.zhihu.com",
        "Referer": "https://www.zhihu.com",
        "User-Agent": agent
    }
    postdata = {
        '_xsrf': '',
        'password': 'SSyn761009',
        'phone_num': '18917918960',
        'captcha': ''
    }

    def parse(self, response):
        """
        提取出页面中所有url,并跟踪这些url进行进一步的爬取
        如果提取的url中格式为 /question/xxx 就下载之后直接进入parse_detail函数
        """
        all_urls = response.css("a::attr(href)").extract()
        all_urls = [parse.urljoin(response.url, url) for url in all_urls]
        # all_urls = filter(lambda x:True if x.startwith("https") else False ,all_urls)
        for url in all_urls:
            match_obj = re.match("(https.*zhihu.com/question/(\d+))(/|$).*", url)
            if match_obj:
                # 如果提取到question页面，交由parse_question提取函数处理
                request_url = match_obj.group(1)
                question_id = int(match_obj.group(2))

                yield scrapy.Request(request_url, headers = self.headers, meta={"question_id":question_id}, callback = self.parse_question)
                break
            else:
                # 如果不是question页面，就进一步跟踪
                # yield scrapy.Request(url, headers=self.headers, callback = self.parse)
                pass

    def parse_question(self, response):
        # 处理question页面， 从页面中提取出具体的question_item
        if "QuestionHeader-title" in response.text:
            # 处理新版本
            question_id = response.meta.get("question_id", "")
            item_loader = ItemLoader(item = ZhihuQuestionItem(), response = response)
            item_loader.add_css("title", "h1.QuestionHeader-title::text")
            #item_loader.add_css("topics", ".QuestionHeader-topics .Popover::text")
            item_loader.add_xpath("topics", "//div[@class='QuestionHeader-topics']//div[@class='Popover']//text()")
            item_loader.add_css("content", ".QuestionHeader-detail")
            item_loader.add_css("answer_num", ".List-headerText span::text")
            item_loader.add_css("comments_num", ".QuestionHeader-Comment button::text")
            item_loader.add_css("watch_user_num", ".NumberBoard-value::text")
            item_loader.add_css("click_num", ".NumberBoard-value::text")
            item_loader.add_value("url", response.url)
            item_loader.add_value("zhihu_id", question_id)

            question_item = item_loader.load_item()
        else:
            # 处理老版本,先假设没有老版本的内容
            print ("========发现老版本的页面========")
        print (self.start_answer_url.format(question_id, 20, 0))

        yield scrapy.Request(self.start_answer_url.format(question_id, 20, 0), headers = self.headers, callback= self.parse_answer)
        #yield question_item


    def parse_answer(self,response):
        # 处理question 的answer
        answer_json = json.loads(response.text)
        is_end = answer_json["paging"]["is_end"]
        next_url = answer_json["paging"]["next"]

        # 提取answer的具体字段
        for answer in answer_json["data"]:
            answer_item = ZhihuAnswerItem()
            answer_item["zhihu_id"] = answer["id"]
            answer_item["url"] = answer["url"]
            answer_item["question_id"] = answer["question"]["id"]
            answer_item["author_id"] = answer["author"]["id"] if "id" in answer["author"] else None
            answer_item["content"] = answer["content"] if "content" in answer else None
            answer_item["praise_num"] = answer["voteup_count"]
            answer_item["comment_num"] = answer["comment_count"]
            answer_item["create_time"] = answer["created_time"]
            answer_item["update_time"] = answer["updated_time"]
            answer_item["crawl_time"] = datetime.datetime.now()

            yield answer_item

        if not is_end:
            yield scrapy.Request(next_url, headers=self.headers, callback=self.parse_answer)




    def start_requests(self):
        return [scrapy.Request('https://www.zhihu.com/#signin', headers = self.headers, callback=self.get_xsrf)]

    def get_xsrf(self, response):
        response_text = response.text
        mathch_obj = re.match('.*name="_xsrf" value="(.*?)"', response_text, re.DOTALL)
        if mathch_obj:
            self.postdata['_xsrf'] = mathch_obj.group(1)
            t = str(int(time.time() * 1000))
            captcha_url = 'https://www.zhihu.com/captcha.gif?r=' + t + "&type=login"
            return [scrapy.Request(
                captcha_url, headers=self.headers, callback=self.get_captcha)]

    def get_captcha(self, response):
        with open('captcha.jpg', 'wb') as f:
            f.write(response.body)
            f.close()
        try:
            im = Image.open('captcha.jpg')
            im.show()
            # im.close()
        except:
            print('find captcha by your self')
        self.postdata['captcha'] = input("please input the captcha\n>").strip()
        if self.postdata['_xsrf'] and self.postdata['captcha']:
            post_url = 'https://www.zhihu.com/login/phone_num'
            return [scrapy.FormRequest(
                url=post_url,
                formdata=self.postdata,
                headers=self.headers,
                callback=self.check_login
            )]

    def check_login(self, response):
        json_text = json.loads(response.text)
        if 'msg' in json_text and json_text['msg'] == '登录成功':
            for url in self.start_urls:
                yield scrapy.Request(url, dont_filter=True, headers=self.headers)  # no callback , turn into parse
