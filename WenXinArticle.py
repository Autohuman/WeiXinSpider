from urllib.parse import urlencode
from pyquery import PyQuery as pq
import requests
import time
import mysql.connector

base_url = 'https://weixin.sogou.com/weixin?'
conn = mysql.connector.connect(
    host='localhost',
    user='root',
    passwd='',
    database='python'
)
cursor = conn.cursor()
insert = "INSERT INTO weixin (title, content, date, orgname, nickname) VALUES(%s, %s, %s, %s, %s)"

headers = {
    'Cookie': 'CXID=9F073E2FB6A2943D08766A5AED514C5E; SUID=F46A4C7C3665860A5C0B8F9D0006BBB9; ad=Ll9lllllll2tjcMNlllllVZUtAtlllllK9e$dlllll9lllllR@RYl@@@@@@@@@@@; IPLOC=CN3100; SUV=1545050739003158; ABTEST=7|1545050744|v1; weixinIndexVisited=1; SUIR=52C3D6E59A9CE7ADB1537D2A9A722B92; ppinf=5|1545052808|1546262408|dHJ1c3Q6MToxfGNsaWVudGlkOjQ6MjAxN3x1bmlxbmFtZToxOi18Y3J0OjEwOjE1NDUwNTI4MDh8cmVmbmljazoxOi18dXNlcmlkOjQ0Om85dDJsdUpyMXZ3VjJBQXZNVmUxVWZ4X1pVREFAd2VpeGluLnNvaHUuY29tfA; pprdig=vOZN43CzmMu2bOoHikL66gJTBdBKljLzjLJzISTDEryCVot1895pn5heCjc7g33YIvXiGKNETg047RGkjn2V3kzeuggxtn8z6hjlmvybpq9MGfvJ18L5px5MnB0MOHAJ7h7CdDNNFPhWFEzOL7fuycJ4TMfgDNah5b4wZu6XRrQ; sgid=06-36288623-AVwXooiaCBOb4q9L7aXvp3zQ; pgv_pvi=926384128; pgv_si=s472145920; ppmdig=15450576310000000b84c05707c8e823bdb7abfec7018fca; PHPSESSID=v3ejcfle7s5jqr54hn2puqppe5; sct=2; JSESSIONID=aaaO6pq398GXF6LXsgaDw; SNUID=E17366552A2F5712FEAB542F2AECAFAD; seccodeRight=success',
    'Host': 'weixin.sogou.com',
    'Referer': 'https://open.weixin.qq.com/connect/qrconnect?appid=wx6634d697e8cc0a29&scope=snsapi_login&response_type=code&redirect_uri=https%3A%2F%2Faccount.sogou.com%2Fconnect%2Fcallback%2Fweixin&state=72a39d2e-393f-44e1-8a22-aa59b052dc56&href=https%3A%2F%2Fdlweb.sogoucdn.com%2Fweixin%2Fcss%2Fweixin_join.min.css%3Fv%3D20170315',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3610.2 Safari/537.36'
}   #设置header以及cookie以规避登录检测

# proxy_pool_url = '127.0.0.1:5000'
#
# proxy = None

# def get_proxy():
#     try:
#         response = requests.get(proxy_pool_url)
#         if response.status_code == 200:
#             return response.text
#         return None
#     except ConnectionError:
#         return None


def get_html(url):  #获取页面html
    try:
        response = requests.get(url, allow_redirects=False, headers = headers)
        if response.status_code == 200:
            return response.text
        if response.status_code == 302:
            #跳转代理
            print('302')
            # proxy = get_proxy()
            # if proxy:
            #     print('Using Proxy', proxy)
            #     return get_html(url)
            # else:
            #     print('Get Proxy Failed')
            #     return None
    except ConnectionError:
        return get_html(url)

def get_index(keyword, page):    #获取索引页，keyword参数设置不同的关键词可以进行不同关键词的索引
    data = {
        'query': keyword,
        'type': 2,
        'page': page
    }
    queries = urlencode(data)
    url = base_url + queries
    html = get_html(url)
    return html

def parse_index(html):   #解析索引页html
    doc = pq(html)
    items = doc('.news-box .news-list li .txt-box h3 a').items()
    for item in items:
        yield item.attr('href')

def get_detail(url):   #获取详情页html
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.text
        return None
    except ConnectionError:
        return None

def parse_detail(html):   #解析详情页html
    doc = pq(html)
    title = doc('.rich_media_title').text()
    content = doc('.rich_media_content').text()
    date = doc('#publish_time').text()
    orgname = doc('#meta_content .rich_media_meta_text').text()
    nickname = doc('#js_name').text()
    return {
        'title': title,
        'content': content,
        'date': date,
        'orgname': orgname,
        'nickname': nickname
    }

def save_to_db(data):   #存储到数据库中
    global cursor
    global insert
    art = (data['title'], data['content'], data['date'], data['orgname'], data['nickname'])
    cursor.execute(insert, art)
    conn.commit()
    print("成功插入一条")

def main():   #主体函数
    for page in range(1,101):
        html = get_index('风景', page)
        if html:
            article_urls = parse_index(html)
            for article_url in article_urls:
                article_html = get_detail(article_url)
                if article_html:
                    article_info = parse_detail(article_html)
                    save_to_db(article_info)
        time.sleep(1)    #通过设置延时来规避爬虫检测，因代理池设置失败
print("结束了")

if __name__ == '__main__':
    main()

