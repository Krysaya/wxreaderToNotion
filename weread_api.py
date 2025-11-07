#!/usr/bin/env python3
import argparse
import json
import logging
import os
import re
import time
import requests
from urllib.parse import parse_qs

WEREAD_URL = "https://weread.qq.com/"
WEREAD_NOTEBOOKS_URL = "https://weread.qq.com/user/notebooks"
WEREAD_BOOKMARKLIST_URL = "https://weread.qq.com/book/bookmarklist"
WEREAD_CHAPTER_INFO = "https://weread.qq.com/book/chapterInfos"
WEREAD_READ_INFO_URL = "https://weread.qq.com/book/readinfo"
WEREAD_REVIEW_LIST_URL = "https://weread.qq.com/review/list"
WEREAD_BOOK_INFO = "https://weread.qq.com/book/info"

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# 解析cookie字符串
def parse_cookie_string(cookie_string):
    cookie_dict = {}
    for item in cookie_string.split('; '):
        if '=' in item:
            key, value = item.split('=', 1)
            cookie_dict[key] = value
    return cookie_dict

# 通用的Notion API请求函数
def notion_api_request(method, endpoint, payload=None, notion_token=None):
    """通用的Notion API请求函数"""
    if notion_token is None:
        notion_token = os.getenv('NOTION_TOKEN')
    
    headers = {
        "Authorization": f"Bearer {notion_token}",
        "Notion-Version": "2025-09-03",
        "Content-Type": "application/json"
    }
    
    url = f"https://api.notion.com/v1{endpoint}"
    
    try:
        if method.upper() == "POST":
            response = requests.post(url, headers=headers, json=payload)
        elif method.upper() == "GET":
            response = requests.get(url, headers=headers)
        elif method.upper() == "PATCH":
            response = requests.patch(url, headers=headers, json=payload)
        else:
            raise ValueError(f"不支持的HTTP方法: {method}")
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Notion API调用失败: {response.status_code}")
            print(f"URL: {url}")
            if response.status_code == 404:
                print("错误: 未找到数据库，请检查数据库ID和集成权限")
            return None
            
    except Exception as e:
        print(f"API请求异常: {e}")
        return None

# 查询数据源
def query_data_source(database_id, filter_condition=None, sorts=None, page_size=1, notion_token=None):
    """查询数据源 - 替换原来的client.databases.query"""
    endpoint = f"/databases/{database_id}/query"
    
    payload = {}
    if filter_condition:
        payload["filter"] = filter_condition
    if sorts:
        payload["sorts"] = sorts
    if page_size:
        payload["page_size"] = page_size
    
    return notion_api_request("POST", endpoint, payload, notion_token)

# 在数据库中创建新页面
def create_page_in_database(database_id, properties, notion_token=None):
    """在数据库中创建新页面"""
    endpoint = "/pages"
    
    payload = {
        "parent": {"database_id": database_id},
        "properties": properties
    }
    
    return notion_api_request("POST", endpoint, payload, notion_token)

# 更新页面属性
def update_page(page_id, properties, notion_token=None):
    """更新页面属性"""
    endpoint = f"/pages/{page_id}"
    payload = {"properties": properties}
    return notion_api_request("PATCH", endpoint, payload, notion_token)

# 获取数据库信息
def get_database_info(database_id, notion_token=None):
    """获取数据库信息"""
    endpoint = f"/databases/{database_id}"
    return notion_api_request("GET", endpoint, notion_token=notion_token)

def get_sort(database_id, notion_token):
    """获取最新的排序值"""
    try:
        print("正在查询最新排序值...")
        
        response = query_data_source(
            database_id=database_id,
            sorts=[{"property": "Sort", "direction": "descending"}],
            page_size=1,
            notion_token=notion_token
        )
        
        if response and response.get("results") and len(response["results"]) > 0:
            latest_page = response["results"][0]
            sort_property = latest_page.get("properties", {}).get("Sort", {})
            
            # 获取排序值
            if sort_property.get("type") == "number":
                sort_value = sort_property.get("number", 0)
                print(f"找到最新排序值: {sort_value}")
                return sort_value
            else:
                print("Sort属性不是数字类型，使用默认值0")
                return 0
        else:
            print("未找到任何记录，使用默认排序值0")
            return 0
            
    except Exception as e:
        print(f"获取排序值时出错: {e}")
        return 0

def check(bookId, database_id, notion_token):
    """检查书籍是否已存在"""
    try:
        filter_condition = {
            "property": "BookId",
            "rich_text": {
                "equals": bookId
            }
        }
        
        print(f"检查书籍是否存在: {bookId}")
        response = query_data_source(
            database_id=database_id,
            filter_condition=filter_condition,
            notion_token=notion_token
        )
        
        if response and response.get("results"):
            results = response["results"]
            if len(results) > 0:
                page_id = results[0]["id"]
                print(f"书籍已存在，找到 {len(results)} 条记录，页面ID: {page_id}")
                return page_id
            else:
                print("书籍不存在")
                return None
        else:
            print("查询失败或返回空结果")
            return None
            
    except Exception as e:
        print(f"检查书籍时出错: {e}")
        return None

def add_book_to_notion(book, sort, database_id, notion_token):
    """添加书籍到Notion"""
    try:
        book_info = book['book']['bookInfo']
        title = book_info.get('title', '未知标题')
        book_id = book_info.get('bookId', '')
        author = book_info.get('author', '未知作者')
        cover = book_info.get('cover', '')
        category = book_info.get('category', '')
        isbn = book_info.get('isbn', '')
        intro = book_info.get('intro', '')
        publisher = book_info.get('publisher', '')
        
        properties = {
            "BookName": {
                "title": [{"text": {"content": title}}]
            },
            "BookId": {
                "rich_text": [{"text": {"content": book_id}}]
            },
            "Sort": {
                "number": sort
            },
            "Author": {
                "rich_text": [{"text": {"content": author}}]
            }
        }
        
        # 可选字段
        if cover:
            properties["Cover"] = {
                "files": [{"name": "cover.jpg", "external": {"url": cover}}]
            }
        if category:
            properties["Category"] = {
                "rich_text": [{"text": {"content": category}}]
            }
        if isbn:
            properties["ISBN"] = {
                "rich_text": [{"text": {"content": isbn}}]
            }
        if intro:
            properties["Intro"] = {
                "rich_text": [{"text": {"content": intro}}]
            }
        if publisher:
            properties["Publisher"] = {
                "rich_text": [{"text": {"content": publisher}}]
            }
        
        response = create_page_in_database(database_id, properties, notion_token)
        
        if response:
            print(f"✅ 成功添加书籍: {title}")
            return True
        else:
            print(f"❌ 添加书籍失败: {title}")
            return False
            
    except Exception as e:
        print(f"添加书籍到Notion时出错: {e}")
        return False

def update_book_in_notion(page_id, book, sort, notion_token):
    """更新Notion中的书籍信息"""
    try:
        properties = {
            "Sort": {"number": sort}
        }
        
        response = update_page(page_id, properties, notion_token)
        
        if response:
            title = book['book']['bookInfo'].get('title', '未知标题')
            print(f"✅ 成功更新书籍排序: {title}")
            return True
        else:
            print(f"❌ 更新书籍失败")
            return False
            
    except Exception as e:
        print(f"更新书籍时出错: {e}")
        return False

    """获取章节信息"""
    body = {
        'bookIds': [bookId],
        'synckeys': [0],
        'teenmode': 0
    }
    r = session.post(WEREAD_CHAPTER_INFO, json=body)
    if r.ok and "data" in r.json() and len(r.json()["data"]) == 1 and "updated" in r.json()["data"][0]:
        update = r.json()["data"][0]["updated"]
        return {item["chapterUid"]: item for item in update}
    return None




def get_bookmark_list(bookId):
    """获取我的划线"""
    params = dict(bookId=bookId)
    r = session.get(WEREAD_BOOKMARKLIST_URL, params=params)
    if r.ok:
        updated = r.json().get("updated")
        updated = sorted(updated, key=lambda x: (
            x.get("chapterUid", 1), int(x.get("range").split("-")[0])))
        return r.json()["updated"]
    return None


def get_read_info(bookId):
    params = dict(bookId=bookId, readingDetail=1,
                  readingBookIndex=1, finishedDate=1)
    r = session.get(WEREAD_READ_INFO_URL, params=params)
    if r.ok:
        return r.json()
    return None


def get_bookinfo(bookId):
    """获取书的详情"""
    params = dict(bookId=bookId)
    r = session.get(WEREAD_BOOK_INFO, params=params)
    isbn = ""
    if r.ok:
        data = r.json()
        isbn = data["isbn"]
        rating = data["newRating"]/1000
    return (isbn, rating)


def get_review_list(bookId):
    """获取笔记"""
    params = dict(bookId=bookId, listType=11, mine=1, syncKey=0)
    r = session.get(WEREAD_REVIEW_LIST_URL, params=params)
    reviews = r.json().get("reviews")
    summary = list(filter(lambda x: x.get("review").get("type") == 4, reviews))
    reviews = list(filter(lambda x: x.get("review").get("type") == 1, reviews))
    reviews = list(map(lambda x: x.get("review"), reviews))
    reviews = list(map(lambda x: {**x, "markText": x.pop("content")}, reviews))
    return summary, reviews


def get_table_of_contents():
    """获取目录"""
    return {
        "type": "table_of_contents",
        "table_of_contents": {
            "color": "default"
        }
    }


def get_heading(level, content):
    if level == 1:
        heading = "heading_1"
    elif level == 2:
        heading = "heading_2"
    else:
        heading = "heading_3"
    return {
        "type": heading,
        heading: {
            "rich_text": [{
                "type": "text",
                "text": {
                    "content": content,
                }
            }],
            "color": "default",
            "is_toggleable": False
        }
    }


def get_quote(content):
    return {
        "type": "callout",
        "callout": {
            "rich_text": [{
                "type": "text",
                "text": {
                    "content": content
                },
            }],
            "color": "default"
        }
    }

def get_callout(content, style, colorStyle, reviewId):

    color = "default"
    # 根据划线颜色设置文字的颜色
    if colorStyle == 1:
        color = "red"
    elif colorStyle == 2:
        color = "purple"
    elif colorStyle == 3:
        color = "blue"
    elif colorStyle == 4:
        color = "green"
    elif colorStyle == 5:
        color = "yellow"
    return {
        "type": "quote",
        "quote": {
            "rich_text": [{
                "type": "text",
                "text": {
                    "content": content,
                }
            }],

            "color": color
        }
    }
def get_notebooklist():
    """获取笔记本列表"""
    r = session.get(WEREAD_NOTEBOOKS_URL)
    if r.ok:
        data = r.json()
        books = data.get("books")
        books.sort(key=lambda x: x["sort"])
        return books
    else:
        print(r.text)
    return None


def get_children(chapter, summary, bookmark_list):
    children = []
    grandchild = {}
    if chapter != None:
        # 添加目录
        children.append(get_table_of_contents())
        d = {}
        for data in bookmark_list:
            chapterUid = data.get("chapterUid", 1)
            if (chapterUid not in d):
                d[chapterUid] = []
            d[chapterUid].append(data)
        for key, value in d .items():
            if key in chapter:
                # 添加章节
                children.append(get_heading(
                    chapter.get(key).get("level"), chapter.get(key).get("title")))
            for i in value:
                callout = get_callout(
                    i.get("markText"), data.get("style"), i.get("colorStyle"), i.get("reviewId"))
                children.append(callout)
                if i.get("abstract") != None and i.get("abstract") != "":
                    quote = get_quote(i.get("abstract"))
                    grandchild[len(children)-1] = quote

    else:
        # 如果没有章节信息
        for data in bookmark_list:
            children.append(get_callout(data.get("markText"),
                            data.get("style"), data.get("colorStyle"), data.get("reviewId")))
    if summary != None and len(summary) > 0:
        children.append(get_heading(1, "点评"))
        for i in summary:
            children.append(get_callout(i.get("review").get("content"), i.get(
                "style"), i.get("colorStyle"), i.get("review").get("reviewId")))
    return children, grandchild

def transform_id(book_id):
    id_length = len(book_id)

    if re.match("^\d*$", book_id):
        ary = []
        for i in range(0, id_length, 9):
            ary.append(format(int(book_id[i:min(i + 9, id_length)]), 'x'))
        return '3', ary

    result = ''
    for i in range(id_length):
        result += format(ord(book_id[i]), 'x')
    return '4', [result]

def calculate_book_str_id(book_id):
    md5 = hashlib.md5()
    md5.update(book_id.encode('utf-8'))
    digest = md5.hexdigest()
    result = digest[0:3]
    code, transformed_ids = transform_id(book_id)
    result += code + '2' + digest[-2:]

    for i in range(len(transformed_ids)):
        hex_length_str = format(len(transformed_ids[i]), 'x')
        if len(hex_length_str) == 1:
            hex_length_str = '0' + hex_length_str

        result += hex_length_str + transformed_ids[i]

        if i < len(transformed_ids) - 1:
            result += 'g'

    if len(result) < 20:
        result += digest[0:20 - len(result)]

    md5 = hashlib.md5()
    md5.update(result.encode('utf-8'))
    result += md5.hexdigest()[0:3]
    return result
# ========== 修改主函数调用方式 ==========

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("weread_cookie")
    parser.add_argument("notion_token")
    parser.add_argument("database_id")
    options = parser.parse_args()
    weread_cookie = options.weread_cookie
    database_id = options.database_id
    notion_token = options.notion_token
    session = requests.Session()
    session.cookies = parse_cookie_string(weread_cookie)
    
    # 删除或注释掉有问题的Client初始化
    # client = Client(
    #     auth=notion_token,
    #     log_level=logging.ERROR
    # )
    
    session.get(WEREAD_URL)
    
    # 修改get_sort调用，传入必要的参数
    latest_sort = get_sort(database_id, notion_token)
    
    books = get_notebooklist()
    if (books != None):
        for book in books:
            sort = book["sort"]
            if sort <= latest_sort:
                continue
            book = book.get("book")
            title = book.get("title")
            cover = book.get("cover")
            bookId = book.get("bookId")
            author = book.get("author")
            
            # 修改check调用，传入必要的参数
            check_result = check(bookId, database_id, notion_token)
            
            chapter = get_chapter_info(bookId)
            bookmark_list = get_bookmark_list(bookId)
            summary, reviews = get_review_list(bookId)
            bookmark_list.extend(reviews)
            bookmark_list = sorted(bookmark_list, key=lambda x: (
                x.get("chapterUid", 1), 0 if x.get("range", "") == "" else int(x.get("range").split("-")[0])))
            isbn,rating = get_bookinfo(bookId)
            children, grandchild = get_children(
                chapter, summary, bookmark_list)
            
            # 修改insert_to_notion调用，传入notion_token
            id = insert_to_notion(title, bookId, cover, sort, author, isbn, rating, database_id, notion_token)
            
            # 修改add_children调用，传入notion_token
            results = add_children(id, children, notion_token)
            
            if(len(grandchild)>0 and results!=None):
                # 修改add_grandchild调用，传入notion_token
                add_grandchild(grandchild, results, notion_token)
# if __name__ == "__main__":
#     parser = argparse.ArgumentParser()
#     parser.add_argument("weread_cookie")
#     parser.add_argument("notion_token")
#     parser.add_argument("database_id")
#     options = parser.parse_args()
#     weread_cookie = options.weread_cookie
#     database_id = options.database_id
#     notion_token = options.notion_token
#     session = requests.Session()
#     session.cookies = parse_cookie_string(weread_cookie)
#     # client = Client(
#     #     auth=notion_token,
#     #     log_level=logging.ERROR
#     # )
#     session.get(WEREAD_URL)
#     latest_sort = get_sort(database_id, notion_token)
#     books = get_notebooklist()
#     if (books != None):
#         for book in books:
#             sort = book["sort"]
#             if sort <= latest_sort:
#                 continue
#             book = book.get("book")
#             title = book.get("title")
#             cover = book.get("cover")
#             bookId = book.get("bookId")
#             author = book.get("author")
#             # check(bookId)
#             check(bookId, database_id, notion_token)
#             chapter = get_chapter_info(bookId)
#             bookmark_list = get_bookmark_list(bookId)
#             summary, reviews = get_review_list(bookId)
#             bookmark_list.extend(reviews)
#             bookmark_list = sorted(bookmark_list, key=lambda x: (
#                 x.get("chapterUid", 1), 0 if x.get("range", "") == "" else int(x.get("range").split("-")[0])))
#             isbn,rating = get_bookinfo(bookId)
#             children, grandchild = get_children(
#                 chapter, summary, bookmark_list)
#             id = insert_to_notion(title, bookId, cover, sort, author,isbn,rating)
#             results = add_children(id, children)
#             if(len(grandchild)>0 and results!=None):
#                 add_grandchild(grandchild, results)
