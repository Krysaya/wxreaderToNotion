#!/usr/bin/env python3
import argparse
import json
import logging
import os
import time
import requests
from urllib.parse import parse_qs

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# ... (您的原有代码，包括 parse_cookie_string、get_bookshelf、get_bookinfo 等函数保持不变) ...

# ========== 以下是需要修改的Notion API相关部分 ==========

def notion_api_request(method, endpoint, payload=None, notion_token=None, timeout=30):
    """
    通用的Notion API请求函数
    使用直接的HTTP请求避免SDK兼容性问题
    """
    headers = {
        "Authorization": f"Bearer {notion_token}",
        "Notion-Version": "2022-06-28",  # 使用稳定的API版本
        "Content-Type": "application/json"
    }
    
    url = f"https://api.notion.com/v1{endpoint}"
    
    try:
        if method.upper() == "POST":
            response = requests.post(url, headers=headers, json=payload, timeout=timeout)
        elif method.upper() == "GET":
            response = requests.get(url, headers=headers, timeout=timeout)
        elif method.upper() == "PATCH":
            response = requests.patch(url, headers=headers, json=payload, timeout=timeout)
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

def query_database(database_id, filter_condition=None, sorts=None, page_size=1, notion_token=None):
    """查询数据库 - 替换原来的client.databases.query"""
    endpoint = f"/databases/{database_id}/query"
    
    payload = {}
    if filter_condition:
        payload["filter"] = filter_condition
    if sorts:
        payload["sorts"] = sorts
    if page_size:
        payload["page_size"] = page_size
    
    return notion_api_request("POST", endpoint, payload, notion_token)

def create_page_in_database(database_id, properties, notion_token=None):
    """在数据库中创建新页面 - 替换原来的client.pages.create"""
    endpoint = "/pages"
    
    payload = {
        "parent": {"database_id": database_id},
        "properties": properties
    }
    
    return notion_api_request("POST", endpoint, payload, notion_token)

def update_page(page_id, properties, notion_token=None):
    """更新页面属性 - 替换原来的client.pages.update"""
    endpoint = f"/pages/{page_id}"
    payload = {"properties": properties}
    return notion_api_request("PATCH", endpoint, payload, notion_token)

# ========== 修改原有的get_sort和check函数 ==========

def get_bookshelf(session):
    """获取微信读书书架"""
    try:
        url = "https://i.weread.qq.com/user/notebooks"
        response = session.get(url)
        if r.ok:
            data = r.json()
            books = data.get("books")
            books.sort(key=lambda x: x["sort"])
            return books
        else:
            print(r.text)
        return None

def get_sort(database_id, notion_token):
    """获取最新的排序值"""
    try:
        response = query_database(
            database_id=database_id,
            sorts=[{"property": "Sort", "direction": "descending"}],
            page_size=1,
            notion_token=notion_token
        )
        
        if response and response.get("results") and len(response["results"]) > 0:
            latest_page = response["results"][0]
            sort_property = latest_page.get("properties", {}).get("Sort", {})
            
            # 保持原有的排序值获取逻辑
            if sort_property.get("type") == "number":
                return sort_property.get("number", 0)
            return 0
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
        
        response = query_database(
            database_id=database_id,
            filter_condition=filter_condition,
            notion_token=notion_token
        )
        
        if response and response.get("results"):
            # 保持原有的返回结构
            return response
        return None
        
    except Exception as e:
        print(f"检查书籍时出错: {e}")
        return None

# ========== 修改原有的书籍添加和更新函数 ==========

def add_book_to_notion(book, sort, database_id, notion_token):
    """添加书籍到Notion - 只修改API调用方式"""
    try:
        # 保持您原有的properties构建逻辑完全不变
        properties = {
            "BookName": {"title": [{"text": {"content": book['book']['bookInfo']['title']}}]},
            "BookId": {"rich_text": [{"text": {"content": book['book']['bookInfo']['bookId']}}]},
            "Sort": {"number": sort},
            "Author": {"rich_text": [{"text": {"content": book['book']['bookInfo']['author']}}]},
            "Cover": {"files": [{"name": "cover.jpg", "external": {"url": book['book']['bookInfo']['cover']}}]},
            "Category": {"rich_text": [{"text": {"content": book['book']['bookInfo']['category']}}]},
            "ISBN": {"rich_text": [{"text": {"content": book['book']['bookInfo']['isbn']}}]},
            "Intro": {"rich_text": [{"text": {"content": book['book']['bookInfo']['intro']}}]},
            "Publisher": {"rich_text": [{"text": {"content": book['book']['bookInfo']['publisher']}}]},
            # ... 您其他的属性定义完全保持不变 ...
        }
        
        # 只修改这行：使用新的API调用方式
        response = create_page_in_database(database_id, properties, notion_token)
        
        if response:
            print(f"✅ 成功添加书籍: {book['book']['bookInfo']['title']}")
            return True
        else:
            print(f"❌ 添加书籍失败: {book['book']['bookInfo']['title']}")
            return False
            
    except Exception as e:
        print(f"添加书籍到Notion时出错: {e}")
        return False

def update_book_in_notion(page_id, book, sort, notion_token):
    """更新Notion中的书籍信息 - 只修改API调用方式"""
    try:
        # 保持您原有的properties构建逻辑
        properties = {
            "Sort": {"number": sort},
            # ... 您其他的更新属性定义保持不变 ...
        }
        
        # 只修改这行：使用新的API调用方式
        response = update_page(page_id, properties, notion_token)
        
        if response:
            print(f"✅ 成功更新书籍排序: {book['book']['bookInfo']['title']}")
            return True
        else:
            print(f"❌ 更新书籍失败: {book['book']['bookInfo']['title']}")
            return False
            
    except Exception as e:
        print(f"更新书籍时出错: {e}")
        return False

# ========== 修改主函数调用方式 ==========

def main(weread_token, notion_token, database_id):
    """主函数 - 只修改Notion相关的调用"""
    try:
        # 您的原有初始化代码保持不变
        session = requests.Session()
        session.cookies.update(parse_cookie_string(weread_token))
        
        # 删除或注释掉原来的client初始化
        # from notion_client import Client
        # client = Client(auth=notion_token, log_level=logging.ERROR)
        
        # 获取最新排序值 - 修改调用方式
        latest_sort = get_sort(database_id, notion_token)
        
        # 获取微信读书书架 - 保持不变
        bookshelf = get_bookshelf(session)
        if not bookshelf:
            print("获取书架失败")
            return
        
        books = bookshelf.get('books', [])
        print(f"一共{len(books)}本，当前是第1本。")
        
        # 同步书籍到Notion - 修改调用方式
        success_count = 0
        for i, book in enumerate(books):
            bookId = book.get('bookId')
            if not bookId:
                continue
                
            print(f"正在同步 {book['title']} ,一共{len(books)}本，当前是第{i+1}本。")
            
            # 检查书籍是否已存在 - 修改调用方式
            response = check(bookId, database_id, notion_token)
            
            if response and response.get("results") and len(response["results"]) > 0:
                # 书籍已存在，更新排序 - 修改调用方式
                page_id = response["results"][0]["id"]
                latest_sort += 1
                if update_book_in_notion(page_id, book, latest_sort, notion_token):
                    success_count += 1
            else:
                # 书籍不存在，添加新书 - 修改调用方式
                latest_sort += 1
                if add_book_to_notion(book, latest_sort, database_id, notion_token):
                    success_count += 1
            
            time.sleep(1)  # 避免请求过于频繁
        
        print(f"同步完成！成功处理 {success_count} 本书籍")
        
    except Exception as e:
        print(f"同步过程出现错误: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("weread_token")
    parser.add_argument("notion_token") 
    parser.add_argument("database_id")
    options = parser.parse_args()
    weread_token = options.weread_token
    database_id = options.database_id
    notion_token = options.notion_token
    
    main(weread_token, notion_token, database_id)