# -*- coding:utf-8 -*-
__author__ = 'Larry'

from scrapy.cmdline import execute
from scrapy.http import Request
import sys, os
#print(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
#sys.stdout = io.TextIOWrapper(sys.stdout.buffer,encoding='utf8') #改变标准输出的默认编码
#execute(["scrapy", "crawl", "jobbole"])
execute(["scrapy", "crawl", "zhihu"])