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

def get_bookshelf(session):
    """获取微信读书书架"""
    try:
        url = "https://i.weread.qq.com/user/notebooks"
        r = session.get(url)
        if r.ok:
            data = r.json()
            books = data.get("books")
            books.sort(key=lambda x: x["sort"])
            return books
        else:
            print(r.text)
        return None
    except Exception as e:
        print(f"获取书架时出错: {e}")
        return None

def get_bookinfo(session, bookId):
    """获取书籍详情"""
    try:
        url = f"https://i.weread.qq.com/book/info?bookId={bookId}"
        r = session.get(url)
        isbn = ""
        if r.ok:
            data = r.json()
            isbn = data["isbn"]
            rating = data["newRating"]/1000
        return (isbn, rating)
    except Exception as e:
        print(f"获取书籍详情时出错: {e}")
        return None

def main(weread_token, notion_token, database_id):
    """主函数"""
    try:
        # 初始化session
        session = requests.Session()
        session.cookies.update(parse_cookie_string(weread_token))
        session.get(WEREAD_URL)

        # 测试Notion连接
        print("测试Notion连接...")
        db_info = get_database_info(database_id, notion_token)
        if not db_info:
            print("❌ Notion连接失败，请检查token和数据库ID")
            return
        
        print("✅ Notion连接成功")
        
        # 获取最新排序值
        latest_sort = get_sort(database_id, notion_token)
        if latest_sort is None:
            latest_sort = 0
        
        # 获取微信读书书架
        print("获取微信读书书架...")
        bookshelf = get_bookshelf(session)
        if not bookshelf:
            print("❌ 获取书架失败")
            return
        
        books = bookshelf.get('books', [])
        print(f"找到 {len(books)} 本书籍")
        
        # 同步书籍到Notion
        success_count = 0
        for i, book in enumerate(books):
            bookId = book.get('bookId')
            if not bookId:
                continue
                
            print(f"\n正在同步第 {i+1}/{len(books)} 本书: {book.get('title', '未知标题')}")
            
            # 检查书籍是否已存在
            existing_page_id = check(bookId, database_id, notion_token)
            
            if existing_page_id:
                # 更新现有书籍
                latest_sort += 1
                if update_book_in_notion(existing_page_id, book, latest_sort, notion_token):
                    success_count += 1
            else:
                # 添加新书籍
                latest_sort += 1
                if add_book_to_notion(book, latest_sort, database_id, notion_token):
                    success_count += 1
            
            # 避免请求过于频繁
            time.sleep(0.5)
        
        print(f"\n🎉 同步完成！成功处理 {success_count}/{len(books)} 本书籍")
        
    except Exception as e:
        print(f"同步过程出现错误: {e}")
        logging.exception("详细错误信息:")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='同步微信读书到Notion')
    parser.add_argument('weread_token', help='微信读书Cookie')
    parser.add_argument('notion_token', help='Notion集成Token')
    parser.add_argument('database_id', help='Notion数据库ID')
    
    args = parser.parse_args()
    
    main(args.weread_token, args.notion_token, args.database_id)