# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html
import codecs, json, MySQLdb
import MySQLdb.cursors
from scrapy.pipelines.images import ImagesPipeline
from scrapy.exporters import JsonItemExporter
from scrapy.exporters import JsonLinesItemExporter
from twisted.enterprise import adbapi

class Py3ScrapyPipeline(object):
    def process_item(self, item, spider):
        return item

#自定义Json，导出到一个文件
class JsonWithEncodingPipeline(object):
    def __init__(self):
        self.file = codecs.open('article.json', 'w', encoding="utf-8")
    def process_item(self, item, spider):
        lines = json.dumps(dict(item), ensure_ascii=False) + "\n"
        self.file.write(lines)
        return item
    def spider_closed(self, spider):
        self.file.close()

#用scrapy 自带的JsonItemExporter导出到一个Json文件
class JsonExporterPipleLine(object):
    def __init__(self):
        self.file = open('articleexporter.json', 'wb')
        self.exporter = JsonItemExporter(self.file, encoding = "utf-8", ensure_ascii=False)
        self.exporter.start_exporting()

    def close_spider(self, spider):
        self.exporter.finish_exporting()
        self.file.close()

    def process_item(self, item, spider):
        self.exporter.export_item(item)
        return item

# 用scrapy 自带的JsonLineItemExporter导出到一个Json文件，每篇文章一行。
class JsonLinesExporterPipleLine(object):
    def __init__(self):
        self.file = open('articlelinesexporter.json', 'wb')
        self.exporter = JsonLinesItemExporter(self.file, encoding="utf-8", ensure_ascii=False)
        self.exporter.start_exporting()

    def close_spider(self, spider):
        self.exporter.finish_exporting()
        self.file.close()

    def process_item(self, item, spider):
        self.exporter.export_item(item)
        return item

#把数据导入到一张jobbole_article mysql表中
class MysqlPipleLine(object):
    def __init__(self):
        self.conn = MySQLdb.connect('127.0.0.1', 'root','Xyjrgss15jqd4f','article_spider', charset="utf8", use_unicode=True)
        self.cursor = self.conn.cursor()
    def process_item(self, item, spider):
        insert_sql = """
                insert into jobbole_article(title, create_date, url, url_object_id, front_image_url, front_image_path, comment_nums, fav_nums, praise_nums, tags, content)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        self.cursor.execute(insert_sql, (item["title"], item["create_date"], item["url"], item["url_object_id"], item["front_image_url"][0], item["front_image_path"], item["comment_nums"], item["fav_nums"], item["praise_nums"], item["tags"], item["content"]))
        self.conn.commit()
        pass

# 把数据通过Twisted 异步导入一张mysql 表中
class MysqlTwistedPipline(object):
    def __init__(self, dbpool):
        self.dbpool = dbpool

    @classmethod
    def from_settings(cls, settings):
        dbparams = dict(
            host = settings["MYSQL_HOST"],
            db = settings["MYSQL_DBNAME"],
            user = settings["MYSQL_USER"],
            passwd = settings["MYSQL_PASSWORD"],
            charset = 'utf8',
            cursorclass = MySQLdb.cursors.DictCursor,
            use_unicode = True,
        )
        dbpool = adbapi.ConnectionPool("MySQLdb", **dbparams)

        return cls(dbpool)

    def do_insert(self, cursor, item):
        #执行具体的插入
        #根据不同的item, 构建不同的sql语句插入到mysql中。

        insert_sql, params = item.get_insert_sql()
        cursor.execute(insert_sql, params)

    def process_item(self, item, spider):
        # 使用twisted ,把mysql insert 变为异步
        query = self.dbpool.runInteraction(self.do_insert, item)
        query.addErrback(self.handle_error, item)

    def handle_error(self, failure, item):
        #处理异步插入异常
        print("===== %s =====" % failure)


# 生成front_image_path（下载图片文件路径）
class ArticleImagePipeline(ImagesPipeline):
    def item_completed(self, results, item, info):
        if "front_image_url" in item:
            for ok, value in results:
                if ok:
                    image_file_path = value["path"]
                else:
                    image_file_path = ""
            item["front_image_path"] = image_file_path
        else:
            item["front_image_path"] = ""
        return item

