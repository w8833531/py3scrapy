# -*- coding:utf-8 -*-
__author__ = 'Larry'

import requests, json, time, os.path, scrapy
try:
    import urlparse as parse
except:
    from urllib import parse

try:
    import cookielib
except:
    import http.cookiejar as cookielib

try:
    from PIL import Image
except:
    pass

session = requests.session()
session.cookies = cookielib.LWPCookieJar(filename="cookies.txt")

class ZhihuSpider(scrapy.Spider):
    name = "zhihu"
    allowed_domains = ["www.zhihu.com"]
    agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.115 Safari/537.36"
    header = {
        "Host": "www.zhihu.com",
        "Referer": "https://www.zhihu.com",
        "User-Agent": agent
    }

    def parse(self, response):
        """
        提取出页面中所有url,并跟踪这些url进行进一步的爬取
        如果提取的url中格式为 /question/xxx 就下载之后直接进入parse_detail函数
        """
        all_urls = response.css("a::attr(href)").extract()
        all_urls = [parse.urljoin(response.url, url) for url in all_urls]
        for url in all_urls:
            pass


    # 获取验证码
    def get_captcha():
        t = str(int(time.time() * 1000))
        captcha_url = 'https://www.zhihu.com/captcha.gif?r=' + t + "&type=login"
        r = session.get(captcha_url, headers=header)
        with open('captcha.jpg', 'wb') as f:
            f.write(r.content)
            f.close()
        # 用pillow 的 Image 显示验证码
        # 如果没有安装 pillow 到源代码所在的目录去找到验证码然后手动输入
        try:
            im = Image.open('captcha.jpg')
            im.show()
            im.close()
        except:
            print(u'请到 %s 目录找到captcha.jpg 手动输入' % os.path.abspath('captcha.jpg'))
        captcha = input("please input the captcha\n>")
        return captcha

    def is_login():
        # 通过个人中心页面返回状态判断是否登录
        inbox_url = "https://www.zhihu.com/inbox"
        response = session.get(inbox_url, headers=header, allow_redirects=False)
        if response.status_code != 200:
            return False
        else:
            return True

    def get_xsrf():
        # 获取xsrf code
        response = session.get("https://www.zhihu.com" ,headers=header)
        match_obj = re.search('.*name="_xsrf" value="(.*?)"', response.text)
        if match_obj:
            return (match_obj.group(1))
        else:
            return ""


    def zhihu_login(account, password):
        # 知乎登录
        if re.match("^1\d{10}", account):
            print ("手机号码登录")
            post_url = "https://www.zhihu.com/login/phone_num"
            post_data = {
                "_xsrf": get_xsrf(),
                "phone_num": account,
                "password": password
            }
        else:
            if "@" in account:
                print("邮箱方式登录")
                post_url = "https://www.zhihu.com/login/email"
                post_data = {
                    "_xsrf": get_xsrf(),
                    "email": account,
                    "password": password
                }
        login_page = session.post(post_url, data=post_data, headers=header)
        login_code = login_page.json()
        if login_code['r'] == 1:
            post_data["captcha"] = get_captcha()
            login_page = session.post(post_url, data=post_data, headers=header)
            login_code = login_page.json()
        session.cookies.save()



# if __name__ == '__main__':
#     if is_login():
#         print('您已经登录')
#     else:
#         account = input('请输入你的用户名\n>  ')
#         password = input("请输入你的密码\n>  ")
#         zhihu_login(account, password)


