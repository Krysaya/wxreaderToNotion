#!/usr/bin/env python3
import argparse
import json
import logging
import os
import re
import time
import requests
from urllib.parse import parse_qs
from datetime import datetime

WEREAD_URL = "https://weread.qq.com/"
WEREAD_NOTEBOOKS_URL = "https://weread.qq.com/api/user/notebook"
WEREAD_BOOKMARKLIST_URL = "https://weread.qq.com/web/book/bookmarklist"
WEREAD_CHAPTER_INFO = "https://weread.qq.com/web/book/chapterInfos"
WEREAD_READ_INFO_URL = "https://weread.qq.com/book/readinfo"
WEREAD_REVIEW_LIST_URL = "https://weread.qq.com/web/review/list"
WEREAD_BOOK_INFO = "https://weread.qq.com/api/book/info"

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

def update_wr_skey_in_cookie(original_cookie, new_wr_skey):
    """更新Cookie中的wr_skey字段"""
    # 将原始Cookie字符串拆分为键值对
    cookie_parts = []
    for item in original_cookie.split(';'):
        item = item.strip()
        if item and '=' in item:
            key, value = item.split('=', 1)
            # 如果找到wr_skey，则更新它
            if key == 'wr_skey':
                cookie_parts.append(f"wr_skey={new_wr_skey}")
            else:
                cookie_parts.append(f"{key}={value}")
    
    # 如果原始Cookie中没有wr_skey，则添加它
    if 'wr_skey' not in original_cookie:
        cookie_parts.append(f"wr_skey={new_wr_skey}")
    
    return '; '.join(cookie_parts)
def refrensh_weread_session(wx_cookie):
    urls_to_visit = [
        'https://weread.qq.com/',
        # 'https://weread.qq.com/web/shelf'
    ]
    updated_cookie = wx_cookie

    for url in urls_to_visit:
        try:
            print(f"r访问: {url}")
            headers = get_headers(wx_cookie)
            response = requests.get(url, headers=headers, timeout=10, allow_redirects=True)
            
            # 正确处理set-cookie头
            print(f"R Set-Cookie头: {response.headers}")

            set_cookie_header = response.headers.get('set-cookie')
            if set_cookie_header:
                print("🔄 服务端返回了新的Cookie")
                # print(f"🔍 Set-Cookie头: {set_cookie_header}")
                
                # 解析新的wr_skey
                if 'wr_skey=' in set_cookie_header:
                    # 从Set-Cookie头中提取wr_skey的值
                    start = set_cookie_header.find('wr_skey=') + 8
                    end = set_cookie_header.find(';', start)
                    if end == -1:
                        end = len(set_cookie_header)
                    new_wr_skey = set_cookie_header[start:end]
                    
                    print(f"✅ 获取到新的wr_skey: {new_wr_skey}")
                    
                    # 更新Cookie中的wr_skey
                    updated_cookie = update_wr_skey_in_cookie(wx_cookie, new_wr_skey)
                    print(f"✅ 更新后的Cookie: {updated_cookie}")



            time.sleep(0.3)
            
        except Exception as e:
            print(f"r 访问 {url} 失败: {e}")
    
    return updated_cookie

# API header模板 - 用于获取笔记、划线等API调用
def get_headers(cookie_str):
    return {
        'Cookie': cookie_str,
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36',
        'Referer': 'https://weread.qq.com/web/shelf',
        'Origin': 'https://weread.qq.com',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    }

# API header模板 - 用于获取笔记、划线等API调用
def get_api_headers(cookie_str, bookId):
    return {
        'Cookie': cookie_str,
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36',
        'Referer': f'https://weread.qq.com/web/reader/{bookId}',
        'Origin': 'https://weread.qq.com',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Sec-Ch-Ua':'"Google Chrome";v="135", "Not-A.Brand";v="8", "Chromium";v="135"',
        'Sec-Ch-Ua-Mobile':'?0',
        'Sec-Ch-Ua-Platform':'"macOS"',
        'Sec-Fetch-Dest':'empty',
        'Sec-Fetch-Mode':'cors',
        'Sec-Fetch-Site':'same-origin',
        
    }
# 通用的Notion API请求函数
def notion_api_request(method, endpoint, payload=None, notion_token=None, timeout=30):
    """通用的Notion API请求函数 - 强制显示错误详情"""
    headers = {
        "Authorization": f"Bearer {notion_token}",
        "Notion-Version": "2022-06-28",
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
            # 🔴 关键：显示完整的错误响应
            print(f"🔴 Notion API调用失败: {response.status_code}")
            print(f"🔴 URL: {url}")
            print(f"🔴 请求头: {headers}")
            print(f"🔴 请求载荷: {json.dumps(payload, indent=2, ensure_ascii=False)}")
            print("🔴 完整错误响应:")
            print(response.text)  # 这行最重要！
            print("🔴" + "="*50)
            return None
            
    except Exception as e:
        print(f"🔴 API请求异常: {e}")
        import traceback
        print(f"🔴 详细异常: {traceback.format_exc()}")
        return None

def query_database(database_id, filter_condition=None, sorts=None, page_size=1, notion_token=None):
    # 查询数据库 - 
    endpoint = f"/databases/{database_id}/query"
    
    # 正确的请求体格式：filter和sorts直接放在顶层
    payload = {
        "page_size": page_size
    }
    
    if filter_condition:
        payload["filter"] = filter_condition  # 直接放在顶层
    if sorts:
        payload["sorts"] = sorts              # 直接放在顶层
    
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
# 查找page
def get_pages(page_id, notion_token):
    """更新页面属性"""
    endpoint = f"/blocks/{page_id}/children"
    return notion_api_request("GET", endpoint, None,notion_token)

# 获取数据库信息
def get_database_info(database_id, notion_token=None):
    """获取数据库信息"""
    endpoint = f"/databases/{database_id}"
    return notion_api_request("GET", endpoint, notion_token=notion_token)

# 获取Notion页面中所有笔记块的唯一标识
def get_existing_note_ids(notion_token,page_id):
    """获取Notion页面中所有笔记块的唯一标识"""
    existing_note_ids = set()
    
    try:
        # 获取页面所有块
        blocks = get_pages(page_id, notion_token)
        results = blocks['results']
        print(f"获取0r : {results[0]} ")

        for i, block in enumerate(results):

            block_type = block.get("type")
            block_id = block.get("id")

            # 只处理callout类型的块（你的笔记块）
            if block_type == "callout":
                existing_note_ids.add(block_id)
                
                # 打印调试信息
                callout_content = block.get("callout", {})
                text_content = ""
                if "text" in callout_content and callout_content["text"]:
                    first_text = callout_content["text"][0]
                    text_content = first_text.get("text", {}).get("content", "")[:30]
                
                print(f"  {i+1}. 找到笔记块: {block_id}")
                print(f"     内容预览: {text_content}...")
        
        print(f"✅ 共找到 {len(existing_note_ids)} 个现有笔记块")
        return existing_note_ids
        
    except Exception as e:
        print(f"❌ 查询现有笔记ID失败: {e}")
        return set()

def get_sort(database_id, notion_token):
    """获取最新的排序值 - 修正获取逻辑"""
    try:
        response = query_database(
            database_id=database_id,
            sorts=[{"property": "Sort", "direction": "descending"}],
            page_size=1,
            notion_token=notion_token
        )
        
        print(f"🔍 排序查询响应: {response}")  # 调试信息
        
        if response and response.get("results") and len(response["results"]) > 0:
            latest_page = response["results"][0]
            sort_property = latest_page.get("properties", {}).get("Sort", {})
            print(f"🔍 Sort属性详情: {sort_property}")  # 调试信息
            
            # 根据数据库：Sort 是 number 类型
            if sort_property.get("type") == "number":
                sort_value = sort_property.get("number")
                print(f"✅ 找到最新排序值: {sort_value}")
                return sort_value if sort_value is not None else 0
            else:
                print(f"⚠️ Sort属性类型不是number: {sort_property.get('type')}")
                return 0
        else:
            print("ℹ️ 未找到任何记录,使用默认排序值0")
            return 0
        
    except Exception as e:
        print(f"❌ 获取排序值时出错: {e}")
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
        response = query_database(
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


    """添加书籍到Notion - 添加数据安全检查"""
    try:
        # 添加数据安全检查
        if 'book' not in book or 'bookInfo' not in book['book']:
            print(f"❌ 书籍数据格式错误: {book}")
            return False
            
        book_info = book['book']['bookInfo']
        
        # 安全地获取各个字段，提供默认值
        title = book_info.get('title', '未知标题')
        book_id = book_info.get('bookId', '')
        author = book_info.get('author', '未知作者')
        cover = book_info.get('cover', '')
        category = book_info.get('category', '')
        isbn = book_info.get('isbn', '')
        intro = book_info.get('intro', '')
        publisher = book_info.get('publisher', '')
        
        properties = {
            "BookName": {"title": [{"text": {"content": title}}]},
            "BookId": {"rich_text": [{"text": {"content": book_id}}]},
            "Sort": {"number": sort},
            "Author": {"rich_text": [{"text": {"content": author}}]},
        }
        
        # 可选字段 - 只在有值时添加
        if cover:
            properties["Cover"] = {"files": [{"name": "cover.jpg", "external": {"url": cover}}]}
        if category:
            properties["Category"] = {"rich_text": [{"text": {"content": category}}]}
        if isbn:
            properties["ISBN"] = {"rich_text": [{"text": {"content": isbn}}]}
        if intro:
            # 如果简介太长，可以截断
            intro_short = intro[:2000] if len(intro) > 2000 else intro
            properties["Intro"] = {"rich_text": [{"text": {"content": intro_short}}]}
        if publisher:
            properties["Publisher"] = {"rich_text": [{"text": {"content": publisher}}]}
        
        response = create_page_in_database(database_id, properties, notion_token)
        
        if response:
            print(f"✅ 成功添加书籍: {title}")
            return True
        else:
            print(f"❌ 添加书籍失败: {title}")
            return False
            
    except Exception as e:
        print(f"添加书籍到Notion时出错: {e}")
        # 打印详细的错误信息以便调试
        import traceback
        print(f"详细错误: {traceback.format_exc()}")
        return False

def add_book_to_notion(book, sort, database_id, notion_token):
    """添加书籍到Notion - 根据实际数据库结构"""
    try:
        if 'book' not in book:
            print(f"❌ 书籍数据格式错误，缺少book字段")
            return False
            
        book_data = book['book']
        title = book_data.get('title', '未知标题')
        book_id = book_data.get('bookId', book.get('bookId', ''))
        author = book_data.get('author', '未知作者')
        cover = book_data.get('cover', 'https://')
        
        # 根据实际数据库结构配置字段类型
        properties = {
            "BookName": {
                "title": [{"text": {"content": title}}]
            },
            "BookId": {
                "rich_text": [{"text": {"content": book_id}}]
            },
            # 根据数据库：Sort 是 number 类型
            "Sort": {
                "number": sort
            },
            "Author": {
                "rich_text": [{"text": {"content": author}}]
            },
            # 根据数据库：Cover 是 files 类型
            "Cover": {
                "files": [{"name": "cover.jpg", "external": {"url": cover}}]
            },
            # 设置默认状态
            "Status": {
                "status": {"name": "未开始"}  # 或者其他可选状态
            }
        }
        
        print(f"🔄 创建页面属性...")
        response = create_page_in_database(database_id, properties, notion_token)
        
        if response:
            print(f"✅ 成功添加书籍: {title}")
            return True
        else:
            print(f"❌ 添加书籍失败: {title}")
            return False
            
    except Exception as e:
        print(f"❌ 添加书籍到Notion时出错: {e}")
        return False
def update_book_in_notion(page_id, book, sort, notion_token):
    """更新Notion中的书籍信息"""
    try:
        # 安全地获取标题
        title = "未知标题"
        if 'book' in book:
            title = book['book'].get('title', '未知标题')
        
        properties = {
            "Sort": {"number": sort}
        }
        
        response = update_page(page_id, properties, notion_token)
            
    except Exception as e:
        print(f"更新书籍时出错: {e}")
        return False

def get_bookshelf(session):
    """获取微信读书书架 - 使用完整的请求头"""
    try:
        url = WEREAD_NOTEBOOKS_URL
        
        # 使用参考项目的完整请求头
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8', 
            'Referer': 'https://weread.qq.com/',
            'Origin': 'https://weread.qq.com'
        }
        
        response = session.get(WEREAD_NOTEBOOKS_URL, headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"获取书架失败: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"获取书架时出错: {e}")
        return None

def get_bookmark_list(session,bookId,wx_cookie):
    """获取划线列表 - 包含章节和划线信息"""
    # new_cookie = refrensh_weread_session(wx_cookie)

    try:
        url = WEREAD_BOOKMARKLIST_URL
        params = {
            'bookId': bookId,
            'synckey':'0'
        }
        print(f"bookid : {bookId}")    

        headers = get_api_headers(wx_cookie,bookId)       
        response = session.get(url, params=params,  timeout=30,headers=headers)

        if response.status_code == 200:
            data = response.json()
            

            # print(f"✅ 获取划线列表成功: {data} ")
            if data.get('errCode') == -2012:

                new_cookie = refrensh_weread_session(wx_cookie)
                session.cookies.update(parse_cookie_string(new_cookie))

                return get_bookmark_list(session,bookId,new_cookie)

            updated = data.get("updated")
            updated = sorted(
                updated,
                key=lambda x: (x.get("chapterUid", 1), int(x.get("range").split("-")[0])),
            )
            return data["updated"]

        
        else:
            print(f"获取划线失败: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"获取划线异常: {e}")
        return None

def get_review_list(session,bookId,wx_cookie):
    """获取笔记列表 - 使用正确的API端点"""

    url = WEREAD_REVIEW_LIST_URL
    params = {
        'bookId': bookId,
        'synckey': 0,
        'mine': 1,
        'listType': 11,

    }
    # 使用参考项目的完整请求头
    # headers = get_api_headers(cookie_str,bookId)           
    headers = get_api_headers(wx_cookie,bookId)       

    response = session.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        reviews = data.get('reviews', [])
        # print(f"✅ 获取笔记列表成功: {data} ")
        if data.get('errCode') == -2012:
            print("❌ 登录超时 (401 + errcode: -2012),需要重新获取Cookie")
             # 直接刷新Cookie
        
            new_token = refrensh_weread_session(wx_cookie)
            # 递归重试
            return get_review_list(session,bookId,new_token)
        
        # 分离总结和笔记
        summary = list(filter(lambda x: x.get("review").get("type") == 4, reviews))
        reviews = list(filter(lambda x: x.get("review").get("type") == 1, reviews))
        reviews = list(map(lambda x: x.get("review"), reviews))
        reviews = list(map(lambda x: {**x, "markText": x.pop("content")}, reviews))

        return summary, reviews


    else:
        print(f"❌ 获取笔记列表失败: {response.status_code} - {response.text}")
        return [], []

def get_read_info(session,bookId):

    params = dict(bookId=bookId, readingDetail=1,
                  readingBookIndex=1, finishedDate=1)
    r = session.get(WEREAD_READ_INFO_URL, params=params)
    if r.ok:
        return r.json()
    return None

def get_bookinfo(session,bookId):
    """获取书籍信息 - 使用正确的API端点"""
    url = f"https://i.weread.qq.com/book/info"
    params = {
        'bookId': bookId
    }        
    # 使用参考项目的完整请求头
    headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8', 
            'Referer': 'https://weread.qq.com/',
            'Origin': 'https://weread.qq.com'
    }

    
    response = session.get(url, params=params, headers=headers)
    if response.status_code == 200:
        data = response.json()
        print(f"🔍 调试 - 响应数据: {data}")

        isbn = data.get('isbn', '')
        rating = data.get('newRating', 0) or data.get('rating', 0)
        print(f"✅ 获取书籍信息成功: ISBN={isbn}, 评分={rating}")
        return isbn, rating
    else:
        print(f"❌ 获取书籍信息失败: {response.status_code} - {response.text}")
        return '', 0

def insert_to_notion(session,bookName, bookId, cover, sort, author,database_id, notion_token):
    """插入到notion-提"""
    time.sleep(0.3)
    parent = {
        "database_id": database_id,
        "type": "database_id"
    }
    properties = {
        "BookName": {"title": [{"type": "text", "text": {"content": bookName}}]},
        "BookId": {"rich_text": [{"type": "text", "text": {"content": bookId}}]},
        # "ISBN": {"rich_text": [{"type": "text", "text": {"content": isbn}}]},
        # "URL": {"url": f"https://weread.qq.com/web/reader/{bookId}"},
        "Author": {"rich_text": [{"type": "text", "text": {"content": author}}]},
        "Sort": {"number": sort},
        # "Rating": {"number": rating},
        "Cover": {"files": [{"type": "external", "name": "Cover", "external": {"url": cover}}]},
    }
    read_info = get_read_info(session,bookId)
    if read_info != None:
        markedStatus = read_info.get("markedStatus", 0)
        readingTime = read_info.get("readingTime", 0)
        format_time = ""
        hour = readingTime // 3600
        if hour > 0:
            format_time += f"{hour}时"
        minutes = readingTime % 3600 // 60
        if minutes > 0:
            format_time += f"{minutes}分"
        properties["Status"] = {"select": {
            "name": "读完" if markedStatus == 4 else "在读"}}
        properties["ReadingTime"] = {"rich_text": [
            {"type": "text", "text": {"content": format_time}}]}
        if "continueBeginDate" in read_info:
            properties["BeginDate"] = {"date": {"start": datetime.utcfromtimestamp(read_info.get(
                "continueBeginDate")).strftime("%Y-%m-%d")}}
        if "finishedDate" in read_info:
            properties["EndDate"] = {"date": {"start": datetime.utcfromtimestamp(read_info.get(
                "finishedDate")).strftime("%Y-%m-%d %H:%M:%S"), "time_zone": "Asia/Shanghai"}}
         

    icon = {
        "type": "external",
        "external": {
            "url": cover
        }
    }
    response = create_page_in_database(database_id, properties, notion_token)
    if response:
        return response.get("id")  # 返回页面ID用于后续添加内容
    return None

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
            "icon": {
                "emoji": "💡"
            },
            "color": "default"
        }
    }

def get_callout(content, style, colorStyle, reviewId):
#     # 根据不同的划线样式设置不同的emoji 直线type=0 背景颜色是1 波浪线是2
    emoji = "🌟"
    if style == 0:
        emoji = "💡"
    elif style == 1:
        emoji = "⭐"
#     # 如果reviewId不是空说明是笔记
    if reviewId != None:
        emoji = "✍️"
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
            # "callout": get_quote(callout_content),
            "color": color
        }
    }

def add_children(page_id, children, notion_token):
    """添加子内容到Notion页面 - 处理分块添加"""
    if not children:
        print("⚠️ 没有子内容需要添加")
        return None
        
    try:
        # Notion API限制每次最多100个子块
        chunk_size = 100
        for i in range(0, len(children), chunk_size):
            chunk = children[i:i + chunk_size]
            
            endpoint = f"/blocks/{page_id}/children"
            payload = {"children": chunk}
            
            print(f"🔄 添加子内容块 {i//chunk_size + 1}/{(len(children)-1)//chunk_size + 1}...")
            response = notion_api_request("PATCH", endpoint, payload, notion_token)
            
            if not response:
                print(f"❌ 添加子内容块失败")
                return None
                
        print(f"✅ 成功添加所有子内容")
        return True
        
    except Exception as e:
        print(f"❌ 添加子内容时出错: {e}")
        return None

def get_children(bookmark_list, summary,reviews):
    children = []
    grandchild = {}
    
    if not bookmark_list:
        return children, grandchild
    
    # 添加目录
    children.append(get_table_of_contents())
    # print(f"笔记📒====--: {bookmark_list}")

    # 按章节UID分组笔记
    chapter_data = {}
    for data in bookmark_list:
        # print(f"📚====-uid===notes-: {data}")

        chapterUid = data.get("chapterUid")
        if chapterUid not in chapter_data:
            chapter_data[chapterUid] = {
                "chapterName": data.get("chapterName", "未知章节"),
                "chapterIdx": data.get("chapterIdx", 0),
                "reviews": [],  # 章节想法
                "notes": [],
            }
        if "author" not in data:
               
            chapter_data[chapterUid]["notes"].append({
                "chapterName": data.get("chapterName", "未知章节"),
                "chapterIdx": data.get("chapterIdx", 0),
                "markText": data.get("markText", ""),
                "style": data.get("style", 0),
                "colorStyle": data.get("colorStyle", 0),
                "bookmarkId": data.get("bookmarkId", ""),
                "range": data.get("range", ""),
                "reviews": [],  # 这个划线笔记对应的想法评论
            })
        # else:
        #     if "abstract" not in data:
        #         chapter_data[chapterUid]["reviews"].append({
        #             "markText": data.get("markText", ""),
        #             # 章节想法
        #         })
            


    for review in reviews:
            chapterUid = review.get("chapterUid", 1)
            # 查找相同章节和范围的划线笔记
            if chapterUid in chapter_data:     
                if "abstract" not in review:
                    
                    if (review.get("chapterName") == chapter_data[chapterUid]["chapterName"]):

                        chapter_data[chapterUid]["reviews"].append({
                            "content": review.get("content", ""),
                            # 章节想法
                        })
                else:
                    for notes in chapter_data[chapterUid]["notes"]:

                        if (review.get("abstract") == notes["markText"]):
                            notes["reviews"].append({
                                "content": review.get("content", "")
                            })
                    
                                
    print(f"组合📚====--: {chapter_data}")
    # 按章节索引排序
    sorted_chapters = sorted(chapter_data.items(), key=lambda x: x[1]["chapterIdx"])
    
    # 处理每个章节
    for chapterUid, chapter_info in sorted_chapters:
        # 添加章节标题
       
        chapter_title = chapter_info["chapterName"]
        level = 2  # 默认使用二级标题
        
        heading_block = get_heading(level, chapter_title)
        children.append(heading_block)
        
        # # 添加该章节下的所有【划线】
        
        for note in chapter_info["notes"]:
            # print(f"🍉 reviews==: {note}")

            callout = get_callout(
                note.get("markText", ""), 
                note.get("style", 0), 
                note.get("colorStyle", 0), 
                note.get("bookmarkId", ""),
            )
            children.append(callout)
            quote = get_quote(
                
            )
         # # 添加该章节下的所有【划线评论】
        
        # for review in chapter_info["reviews"]:
        #     print(f"🍉 reviews==: {review}")

        #     callout = get_quote(
        #         note.get("abstract", "")
        #     )
        #     children.append(callout)    
        
     # 处理想法 (reviews)
    # if reviews and len(reviews) > 0:
    #     children.append(get_heading(1, "想法"))
        
    #     # 按章节分组想法
    #     review_chapter_data = {}
    #     for review in reviews:
    #         chapterUid = review.get("chapterUid", 1)
    #         if chapterUid not in review_chapter_data:
    #             review_chapter_data[chapterUid] = {
    #                 "chapterName": review.get("chapterName", f"章节{chapterUid}"),
    #                 "reviews": []
    #             }
    #         review_chapter_data[chapterUid]["reviews"].append(review)
        
    #     # 按chapterIdx排序
    #     sorted_review_chapters = sorted(review_chapter_data.items(), key=lambda x: x[1]["reviews"][0].get("chapterIdx", 0))

    #     for chapterUid, chapter_info in sorted_review_chapters:
    #         # 添加想法章节标题
    #         chapter_title = chapter_info["chapterName"]
    #         children.append(get_heading(3, f"{chapter_title} - 想法"))
            
    #         # 添加该章节的想法
    #         for review in chapter_info["reviews"]:
    #             callout = get_quote(
    #                 review.get("content", "")
    #             )
    #             children.append(callout)
                
                # 处理想法的摘要
                # abstract = review.get("abstract")
                # if abstract and abstract.strip():
                #     quote = get_quote(abstract)
                #     grandchild[len(children)-1] = quote


    # 添加点评部分
    if summary and len(summary) > 0:
        children.append(get_heading(1, "点评"))
        for i in summary:
            review_content = i.get("review", {}).get("content", "")
            if review_content and review_content.strip():
                children.append(get_callout(
                    review_content, 
                    i.get("style", 0),
                    i.get("colorStyle", 0),
                    i.get("review", {}).get("reviewId", "")
                ))
    
    print(f"✅ 最终生成的=== :{children}")
    return children, grandchild

def main(weread_token, notion_token, database_id):

    """主函数 - 添加错误处理和提前退出"""
    try:
        # # 初始化session和Notion API
        session = requests.Session()
        session.cookies.update(parse_cookie_string(weread_token))
        

        # 原有的同步逻辑，但现在数据获取函数会自己处理Cookie刷新
        latest_sort = get_sort(database_id, notion_token)
        if latest_sort is None:
            print("❌ 获取排序值失败，停止同步")
            exit(1)

        # 获取微信读书书架
        print("获取微信读书书架...")
        bookshelf = get_bookshelf(session)
        if not bookshelf:
            print("❌ 获取书架失败，停止同步")
            return

        books = bookshelf.get('books', [])

        # 5. 同步书籍到Notion - 整合完整功能
        success_count = 0
        error_count = 0
        max_errors = 1  # 最大错误次数
        
        for i, book in enumerate(books):
            # 原有的书籍基本信息处理
            book_id = book.get('bookId')
            cover = 'http'
            if book.get('cover'):
                cover = book.get('cover')
            sort = book["sort"]
            author = book.get("author")
            if not book_id:
                print("❌ 书籍ID缺失,跳过")
                error_count += 1
                if error_count >= max_errors:
                    print("❌ 错误次数超过限制，停止同步")
                    break
                continue
                
            title = book.get('title', '未知标题')
            print(f"book==: {book}")
            print(f"\n正在处理 [{i+1}/{len(books)}]: {title}")
            
            # 检查书籍是否已存在
            existing_page_id = check(book_id, database_id, notion_token)
            
            try:
                if existing_page_id:
                    # 更新现有书籍 - 同时添加或更新内容
                    latest_sort += 1
                    
                    # 获取详细数据用于更新内容

                    bookmark_list = get_bookmark_list(session,book_id,weread_token)                    
                    summary, reviews = get_review_list(session,book_id,weread_token)
                    bookmark_list.extend(reviews)
                    # print(f"✅ reviews=-==: {reviews}")
                    
                    # 排序内容
                    bookmark_list = sorted(bookmark_list, key=lambda x: (
                        x.get("chapterUid", 1), 
                        0 if x.get("range", "") == "" else int(x.get("range").split("-")[0])
                    ))
                    # 2. 获取该页面上已存在的笔记ID
                    existing_note_ids = get_existing_note_ids(notion_token, existing_page_id)
                    print(f"🔄 书籍已存在ID,更新内容: {existing_note_ids}")
                    
                    # 构建内容

                    children, grandchild = get_children(bookmark_list, summary, reviews)
                    return
                    # 检查是否有内容生成
                    if not children:
                        print(f"❌ 没有生成任何内容块，跳过书籍: {title}")
                        error_count += 1
                        if error_count >= max_errors:
                            print("❌ 错误次数超过限制，停止同步")
                            break
                        continue
                    
                    print(f"✅ 成功生成 :{grandchild}")

                    results = add_children(existing_page_id, children,notion_token)

                    # 然后添加内容
                    print(f"📚 为已存在书籍添加内容...")
                    if not results:
                        print(f"❌ 为已存在书籍添加内容失败: {title}")
                        error_count += 1
                        if error_count >= max_errors:
                            print("❌ 错误次数超过限制，停止同步")
                            break
                        continue
                        
                    success_count += 1
                    print(f"✅ 成功更新书籍内容: {title}")
                   
                  
                else:
                    # 新增完整功能：获取详细数据并创建完整页面
                    latest_sort += 1
                 
                    
                    # 获取划线列表
                    print(f"📝 获取划线列表...")
                    bookmark_list = get_bookmark_list(session,book_id,weread_token)
                    if bookmark_list is None:
                        print(f"❌ 获取划线列表失败: {title}")
                        error_count += 1
                        if error_count >= max_errors:
                            print("❌ 错误次数超过限制，停止同步")
                            break
                        continue
                    
                    # 获取笔记和评论
                    print(f"💭 获取笔记和评论...")
                    summary, reviews = get_review_list(session,book_id,weread_token)
                    bookmark_list.extend(reviews)
                    
                    # 排序内容
                    bookmark_list = sorted(bookmark_list, key=lambda x: (
                        x.get("chapterUid", 1), 
                        0 if x.get("range", "") == "" else int(x.get("range").split("-")[0])
                    ))
                    
                    # 获取书籍详细信息
                    # isbn, rating = get_bookinfo(session,book_id)
                    
                    # 构建内容结构
                    children, grandchild = get_children(bookmark_list, summary, reviews)
                    # 检查是否有内容生成
                    if not children:
                        print(f"❌ 没有生成任何内容块，跳过书籍: {title}")
                        error_count += 1
                        if error_count >= max_errors:
                            print("❌ 错误次数超过限制，停止同步")
                            break
                        continue

                    print(f"✅ 成功生成 {len(children)} 个内容块")

                    # 创建Notion页面 - 使用原有的add_book_to_notion函数
                    print(f"🔄 创建Notion页面...")
                    page_id = insert_to_notion(session,title, book_id, book.get('cover', ''), latest_sort, 
                                            book.get('author', '') , database_id, notion_token)
                    if not page_id:
                        print(f"❌ 创建Notion页面失败: {title}")
                        error_count += 1
                        if error_count >= max_errors:
                            print("❌ 错误次数超过限制，停止同步")
                        break

                    # 添加详细内容（目录、笔记、划线等）
                    print(f"📚 添加详细内容...")
                    if children:  # 只有在有内容时才添加
                        results = add_children(page_id, children, notion_token)
                        if not results:
                            print(f"⚠️ 添加子内容失败: {title}，但书籍页面已创建")
                    else:
                        print(f"ℹ️ 没有找到章节或笔记内容: {title}")

                    success_count += 1
                    print(f"✅ 成功添加完整书籍: {title}")
                
                # 检查错误计数
                if error_count >= max_errors:
                    print("❌ 错误次数超过限制，停止同步")
                    break
                    
            except Exception as e:
                error_count += 1
                print(f"❌ 处理书籍时发生异常: {title} - {e}")
                if error_count >= max_errors:
                    print("❌ 错误次数超过限制，停止同步")
                    break
            
            # 避免请求过于频繁
            time.sleep(1)
        
        print(f"\n🎉 同步完成！成功: {success_count}, 失败: {error_count}, 总计: {len(books)}")
        
        
    except Exception as e:
        print(f"❌ 同步过程出现严重错误: {e}")
        return

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='同步微信读书到Notion')
    parser.add_argument('weread_token', help='微信读书Cookie')
    parser.add_argument('notion_token', help='Notion集成Token')
    parser.add_argument('database_id', help='Notion数据库ID')
    
    args = parser.parse_args()
    
    main(args.weread_token, args.notion_token, args.database_id)