# -*- coding: utf-8 -*-
from urllib import parse

import scrapy
from scrapy.http import Request

from py3scrapy.items import JobBoleArticleItem, ArticleItemLoad
from py3scrapy.utils.common import get_md5


class JobboleSpider(scrapy.Spider):
    name = 'jobbole'
    allowed_domains = ['blog.jobbole.com']
    start_urls = ['http://blog.jobbole.com/all-posts']

    def parse(self, response):
        """
        1.获取文章列表页面中的文章URL并交给scrapy 进行下载解析
        2.获取下一页的url,并交给Scrapy进行下载解析
        """
        post_nodes = response.css("div.floated-thumb .post-thumb a")
        for post_node in post_nodes:
            image_url = post_node.css("img::attr(src)").extract_first("")
            image_url = parse.urljoin(response.url, image_url)
            post_url = post_node.css("::attr(href)").extract_first("")
            # post_url = "http://blog.jobbole.com/109905/"
            yield Request(url=parse.urljoin(response.url, post_url), meta={"front_image_url": image_url},
                          callback=self.parse_detail)

        # 提取下一页，让scrapy 下载
        next_url = response.css(".next.page-numbers::attr(href)").extract_first("")
        if next_url:
            yield Request(url=parse.urljoin(response.url, next_url), callback=self.parse)

    def parse_detail(self, response):
        article_item = JobBoleArticleItem()
        # ##使用xpath 进行解析
        # title = response.xpath('//div[@class="entry-header"]/h1/text()').extract()[0]
        # create_date = response.xpath("//p[@class='entry-meta-hide-on-mobile']/text()").extract()[0].strip().replace("·",'').strip()
        # tag_list = response.xpath("//p[@class='entry-meta-hide-on-mobile']/a/text()").extract()
        # tag_list = [element for element in tag_list if not element.strip().endswith("评论")]
        # tags = ','.join(tag_list)
        # content = response.xpath("//div[@class='entry']").extract()[0]
        # praise_nums = response.xpath("//span[contains(@class, 'vote-post-up')]/h10/text()").extract()[0]
        # fav_nums =  response.xpath("//span[contains(@class, 'bookmark-btn')]/text()").extract()[0]
        # match_re = re.match(".*?(\d).*", fav_nums)
        # if match_re:
        #    fav_nums = match_re.group(1)
        # else:
        #    fav_nums = '0'
        # comment_nums = response.xpath("//a[@href='#article-comment']/span/text()").extract()[0]
        # match_re = re.match(".*?(\d).*", comment_nums)
        # if match_re:
        #    comment_nums = match_re.group(1)
        # else:
        #    comment_nums = '0'

        ####通过css 选择器来进行解析，提取文章的具体字段
        # title = response.css(".entry-header h1::text").extract()[0]
        # create_date = response.css("p.entry-meta-hide-on-mobile::text").extract()[0].strip().replace("·",'').strip()
        # try:
        #     create_date = datetime.datetime.strptime(create_date, "%Y/%m/%d").date()
        # except Exception as e:
        #     create_date = datetime.datetime.now().date()
        # praise_nums = int(response.css(".vote-post-up h10::text").extract()[0])
        # fav_nums = response.css(".bookmark-btn::text").extract()[0]
        # match_re = re.match(".*?(\d).*", fav_nums)
        # if match_re:
        #     fav_nums = int(match_re.group(1))
        # else:
        #     fav_nums = 0
        # comment_nums = response.css("a[href='#article-comment'] span::text").extract()[0]
        # match_re = re.match(".*?(\d).*", comment_nums)
        # if match_re:
        #     comment_nums = int(match_re.group(1))
        # else:
        #     comment_nums = 0
        # content = response.css("div.entry").extract()[0]
        # tag_list = response.css("p.entry-meta-hide-on-mobile a::text").extract()
        # tag_list = [element for element in tag_list if not element.strip().endswith("评论")]
        # tags = ','.join(tag_list)
        # #把上面的值传递给item
        # article_item["url_object_id"] = get_md5(response.url)
        # article_item["url"] = response.url
        # article_item["title"] = title
        # article_item["front_image_url"] = [front_image_url]
        # article_item["create_date"] = create_date
        # article_item["praise_nums"] = praise_nums
        # article_item["fav_nums"] = fav_nums
        # article_item["comment_nums"] = comment_nums
        # article_item["tags"] = tags
        # article_item["content"] = content

        """
        变量定义说明  ：
        front_image_url   str   文章封面图URL
        title   str  文章标题
        create_date   str   文章生成时间
        praise_nums   int  文章点赞数
        fav_nums    int  文章收藏数
        comment_nums   int  文章评论数
        content   str  文章内容
        tags   str 文章标签列表
        """

        # 通过重载过itemloader的ArticleItemLoad 加载item
        front_image_url = response.meta.get("front_image_url", "")
        item_loader = ArticleItemLoad(item=JobBoleArticleItem(), response=response)
        item_loader.add_xpath("title", "//div[@class='entry-header']/h1/text()")
        item_loader.add_xpath("create_date", "//div[@class='entry-meta']/p[@class='entry-meta-hide-on-mobile']/text()")
        item_loader.add_xpath("praise_nums",
                              "//span[contains(@class, 'vote-post-up')]/h10/text() | //span[contains(@class, 'vote-post-up')]/text()")
        item_loader.add_xpath("fav_nums", "//span[contains(@class,  'bookmark-btn')]/text()")
        item_loader.add_xpath("comment_nums", "//a[@href='#article-comment']/span/text()")
        item_loader.add_xpath("tags", "//p[@class='entry-meta-hide-on-mobile']/a/text()")
        item_loader.add_xpath("content", "//div[@class='entry']")
        item_loader.add_value("url", response.url)
        item_loader.add_value("url_object_id", get_md5(response.url))
        item_loader.add_value("front_image_url", [front_image_url])
        article_item = item_loader.load_item()

        yield article_item

        pass
