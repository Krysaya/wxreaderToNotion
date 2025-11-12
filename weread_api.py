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

# 获取数据库信息
def get_database_info(database_id, notion_token=None):
    """获取数据库信息"""
    endpoint = f"/databases/{database_id}"
    return notion_api_request("GET", endpoint, notion_token=notion_token)

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
        cover = book_data.get('cover', '')
        
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
        
        if response:
            print(f"✅ 成功更新书籍排序: {title}")
            return True
        else:
            print(f"❌ 更新书籍失败: {title}")
            return False
            
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
    try:
        url = WEREAD_BOOKMARKLIST_URL
        params = {
            'bookId': bookId,
        }
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': f'https://weread.qq.com/web/reader/{bookId}',
            'Origin': 'https://weread.qq.com',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        }
        
        print(f"🔍 调试 - 请求划线列表: {url}")
        
        response = session.get(url, params=params, headers=headers, timeout=30)
        print(f"🔍 调试 - 响应状态: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"🔍 调试 - 完整响应数据: {data}")
            
            # 获取章节信息
            chapters = data.get('chapters', [])
            bookmarks = data.get('updated', [])
            
            print(f"✅ 获取数据成功: {len(chapters)} 个章节, {len(bookmarks)} 条划线")
            
            # 返回章节和划线数据
            return {
                'chapters': chapters,
                'bookmarks': bookmarks
            }
        elif response.status_code == 401:
            # 状态码401表示未授权
            data = response.json()
            if data.get('errcode') == -2012:
                print("❌ 登录超时 (401 + errcode: -2012),需要重新获取Cookie")
                # 直接刷新Cookie
                new_cookie = refresh_session(wx_cookie)
                if new_cookie == wx_cookie:
                    print("🔄 Cookie未更新,跳过重试")
                    return [], []
                else:
                    # 递归重试
                    return get_bookmark_list(session,bookId, new_cookie)
            else:
                print(f"❌ 其他授权错误: {data}")
                return [], []
        else:
            print(f"❌ 获取划线失败: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ 获取划线异常: {e}")
        return None

def get_review_list(session,bookId,wx_cookie):
    """获取笔记列表 - 使用正确的API端点"""
    url = f"https://i.weread.qq.com/review/list"
    params = {
        'bookId': bookId,
        'listType': 11,
        'mine': 1,
        'synckey': 0,
        'listMode': 0
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
        reviews = data.get('reviews', [])
        print(f"✅ 获取笔记列表成功: {len(reviews)} 条笔记")
        
        # 分离总结和笔记
        summary = [r for r in reviews if r.get('review', {}).get('type') == 4]
        other_reviews = [r for r in reviews if r.get('review', {}).get('type') != 4]
        return summary, other_reviews

    elif response.status_code == 401:
        # 状态码401表示未授权
        data = response.json()
        if data.get('errcode') == -2012:
            print("❌ 登录超时 (401 + errcode: -2012)，需要重新获取Cookie")
             # 直接刷新Cookie
        
            new_cookie = refresh_session(wx_cookie)
            if new_cookie == wx_cookie:
                print("🔄 Cookie未更新,跳过重试")
                return [], []
            else:
                # 递归重试
                return get_review_list(session,bookId,new_cookie)
        
        else:
            print(f"❌ 未授权错误: {response.status_code} - {data}")
        return [], []

    else:
        print(f"❌ 获取笔记列表失败: {response.status_code} - {response.text}")
        return [], []

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

def get_chapter_info(session,bookId):
    
    """获取章节信息 - 添加类型检查"""
    print(f"🔍 调试 - session类型: {type(session)}")
    print(f"🔍 调试 - session是否有post方法: {hasattr(session, 'post')}")
    
    if not hasattr(session, 'post'):
        print(f"❌ 错误: session参数不是有效的Session对象")
        return None
        
    """获取章节信息 - 使用正确的API端点"""
    url = f"https://i.weread.qq.com/book/chapterInfos"
    params = {
        'bookIds': [bookId],
        'synckeys': [0]
    }
    headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8', 
            'Referer': 'https://weread.qq.com/web/reader/${bookId}',
            'Origin': 'https://weread.qq.com'
    }
    
    response = session.post(url, json=params, headers=headers)
    if response.status_code == 200:
        data = response.json()
        if data and 'data' in data and bookId in data['data']:
            chapter_info = data['data'][bookId]
            print(f"✅ 获取章节信息成功: {len(chapter_info.get('updated', []))} 个章节")
            return chapter_info
        else:
            print("⚠️ 章节数据格式异常")
            return None
    else:
        print(f"❌ 获取章节信息失败: {response.status_code} - {response.text}")
        return None

def insert_to_notion(title, bookId, cover, sort, author, isbn, rating, database_id, notion_token):
    """插入书籍到Notion - 只创建基础页面，不添加内容"""
    properties = {
        "BookName": {"title": [{"text": {"content": title}}]},
        "BookId": {"rich_text": [{"text": {"content": bookId}}]},
        "Sort": {"number": sort},
        "Author": {"rich_text": [{"text": {"content": author}}]},
        "Cover": {"files": [{"name": "cover.jpg", "external": {"url": cover}}]},
    }
    
    if isbn:
        properties["ISBN"] = {"rich_text": [{"text": {"content": isbn}}]}
    
    response = create_page_in_database(database_id, properties, notion_token)
    if response:
        return response.get("id")  # 返回页面ID用于后续添加内容
    return None

def get_children(bookmark_data, summary, reviews):
    """构建子内容 - 使用新的数据结构"""
    children = []
    
    chapters = bookmark_data.get('chapters', [])
    bookmarks = bookmark_data.get('bookmarks', [])
    
    print(f"🔍 调试 - 章节数量: {len(chapters)}")
    print(f"🔍 调试 - 划线数量: {len(bookmarks)}")
    print(f"🔍 调试 - 总结数量: {len(summary)}")
    print(f"🔍 调试 - 笔记数量: {len(reviews)}")
    
    # 检查是否有任何有效数据
    has_chapters = len(chapters) > 0
    has_bookmarks = len(bookmarks) > 0
    has_summary = len(summary) > 0
    has_reviews = len(reviews) > 0
    
    if not any([has_chapters, has_bookmarks, has_summary, has_reviews]):
        print("❌ 没有找到任何章节、划线、总结或笔记数据")
        return [], {}
    
    # 添加基础标题
    children.append({
        "object": "block",
        "type": "heading_1",
        "heading_1": {
            "rich_text": [{"type": "text", "text": {"content": "📚 阅读笔记"}}]
        }
    })
    
    # 处理目录结构
    if has_chapters:
        print(f"🔍 调试 - 处理章节: {len(chapters)}个")
        
        children.append({
            "object": "block", 
            "type": "heading_1",
            "heading_1": {
                "rich_text": [{"type": "text", "text": {"content": "📖 章节目录"}}]
            }
        })
        
        for i, chap in enumerate(chapters[:10]):  # 限制数量避免过大
            level = chap.get('level', 1)
            chap_title = chap.get('title', '')
            chap_uid = chap.get('chapterUid', '')
            
            print(f"🔍 调试 - 章节{i+1}: 级别{level}, 标题: {chap_title}")
            
            if level == 1:
                children.append({
                    "object": "block",
                    "type": "heading_2",
                    "heading_2": {
                        "rich_text": [{"type": "text", "text": {"content": f"{i+1}. {chap_title}"}}]
                    }
                })
            elif level == 2:
                children.append({
                    "object": "block",
                    "type": "heading_3",
                    "heading_3": {
                        "rich_text": [{"type": "text", "text": {"content": f"  {i+1}. {chap_title}"}}]
                    }
                })
    
    # 处理总结
    if has_summary:
        print(f"🔍 调试 - 处理总结: {len(summary)}条")
        
        children.append({
            "object": "block",
            "type": "heading_1",
            "heading_1": {
                "rich_text": [{"type": "text", "text": {"content": "💡 读书总结"}}]
            }
        })
        for i, s in enumerate(summary):
            content = s.get('review', {}).get('content', '')
            if content:
                children.append({
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [{"type": "text", "text": {"content": content}}]
                    }
                })
    
    # 处理笔记和划线
    all_marks = bookmarks + reviews
    if all_marks:
        print(f"🔍 调试 - 处理划线笔记: {len(all_marks)}条")
        
        children.append({
            "object": "block",
            "type": "heading_1", 
            "heading_1": {
                "rich_text": [{"type": "text", "text": {"content": "📝 笔记与划线"}}]
            }
        })
        
        # 按章节分组
        chapter_marks = {}
        for mark in all_marks:
            chapter_uid = mark.get('chapterUid', '')
            if chapter_uid not in chapter_marks:
                chapter_marks[chapter_uid] = []
            chapter_marks[chapter_uid].append(mark)
        
        # 按章节顺序处理
        for chap in chapters:
            chapter_uid = chap.get('chapterUid', '')
            if chapter_uid in chapter_marks:
                # 添加章节标题
                children.append({
                    "object": "block",
                    "type": "heading_2",
                    "heading_2": {
                        "rich_text": [{"type": "text", "text": {"content": chap.get('title', '')}}]
                    }
                })
                
                # 添加该章节的划线和笔记
                for mark in chapter_marks[chapter_uid]:
                    content = mark.get('markText', '') or mark.get('content', '')
                    if content:
                        children.append({
                            "object": "block",
                            "type": "quote",
                            "quote": {
                                "rich_text": [{"type": "text", "text": {"content": content}}]
                            }
                        })
    
    print(f"🔍 调试 - 最终生成的子块数量: {len(children)}")
    return children, {}

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

def update_cookie_from_response(current_cookie, set_cookie_headers):
    """从响应头更新Cookie"""
    print(f"🔄 更新Cookie字段当前ck头: {set_cookie_headers}")

    cookie_dict = {}
    
    # 解析当前Cookie
    for item in current_cookie.split('; '):
        if '=' in item:
            key, value = item.split('=', 1)
            cookie_dict[key.strip()] = value
    
    # 更新新Cookie
    for set_cookie in set_cookie_headers:
        # 取第一个分号前的内容
        cookie_parts = set_cookie.split(';')[0].strip()
        if '=' in cookie_parts:
            key, value = cookie_parts.split('=', 1)
            key = key.strip()
            if key:  # 确保键名不为空
                cookie_dict[key] = value
                print(f"🔄 更新Cookie字段: {key}")
            else:
                print(f"⚠️ 跳过空的Cookie键名")
        else:
            print(f"⚠️ 无效的Cookie格式: {cookie_parts}")
    
    # 重新构建Cookie字符串
    new_cookie = '; '.join([f"{k}={v}" for k, v in cookie_dict.items()])
    return new_cookie

def refresh_session(current_cookie):
    """刷新微信读书会话"""
    print("🔄 正在刷新微信读书会话...")
    
    urls_to_visit = [
        'https://weread.qq.com/',  # 首页
        'https://weread.qq.com/web/shelf',  # 书架页
    ]
    
    updated_cookie = current_cookie
    
    for url in urls_to_visit:
        try:
            print(f"🔍 访问: {url}")
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Cookie': updated_cookie,
                'Referer': 'https://weread.qq.com/',
            }
            
            response = requests.get(url, headers=headers, timeout=10, allow_redirects=True)
            print(f"刷新cookie返回的header: {response.headers}")

            # 检查是否有新Cookie
            if 'set-cookie' in response.headers:
                set_cookie_headers = response.headers.get('set-cookie')
                if set_cookie_headers:
                    print("🔄 服务端返回了新的Cookie")
                    updated_cookie = update_cookie_from_response(updated_cookie, set_cookie_headers)
            
            time.sleep(0.3)
            
        except Exception as e:
            print(f"❌ 访问 {url} 失败: {e}")
    
    return updated_cookie
def main(weread_token, notion_token, database_id):
    """主函数 - 添加错误处理和提前退出"""
    try:
        # 初始化session和Notion API
        session = requests.Session()
        session.cookies.update(parse_cookie_string(weread_token))
        
        # 设置微信读书请求头
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Referer': 'https://weread.qq.com/',
            'Origin': 'https://weread.qq.com',
        })
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
        print(f"找到 {len(books)} 本书籍需要同步")

        # 5. 同步书籍到Notion - 整合完整功能
        success_count = 0
        error_count = 0
        max_errors = 3  # 最大错误次数
        
        for i, book in enumerate(books):
            # 原有的书籍基本信息处理
            book_id = book.get('bookId')
            if not book_id:
                print("❌ 书籍ID缺失,跳过")
                error_count += 1
                if error_count >= max_errors:
                    print("❌ 错误次数超过限制，停止同步")
                    break
                continue
                
            title = book.get('title', '未知标题')
            print(f"\n正在处理 [{i+1}/{len(books)}]: {title}")
            
            # 检查书籍是否已存在
            existing_page_id = check(book_id, database_id, notion_token)
            
            try:
                if existing_page_id:
                    # 更新现有书籍 - 同时添加或更新内容
                    print(f"🔄 书籍已存在，更新内容: {title}")
                    latest_sort += 1
                    
                    # 获取详细数据用于更新内容
                    # print(f"📖 获取章节信息...")
                    # chapter = get_chapter_info(session,book_id)
                    
                    print(f"📝 获取划线列表...")
                    bookmark_list = get_bookmark_list(session,book_id,weread_token)
                    
                    print(f"💭 获取笔记和评论...")
                    summary, reviews = get_review_list(session,book_id,weread_token)
                    # bookmark_list.extend(reviews)
                    
                    # 排序内容
                    bookmark_list = sorted(bookmark_list, key=lambda x: (
                        x.get("chapterUid", 1), 
                        0 if x.get("range", "") == "" else int(x.get("range").split("-")[0])
                    ))
                    
                    # 构建内容
                    print(f"🔨 构建内容结构...")
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
                    
                    # 先更新排序
                    if update_book_in_notion(existing_page_id, book, latest_sort, notion_token):
                        print(f"✅ 成功更新书籍排序: {title}")
                    else:
                        print(f"❌ 更新书籍排序失败: {title}")
                    
                    # 然后添加内容
                    print(f"📚 为已存在书籍添加内容...")
                    results = add_children(existing_page_id, children, notion_token)
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
                    
                    # # 获取章节信息
                    # print(f"📖 获取章节信息...")
                    # chapter = get_chapter_info(session,book_id)
                    # if chapter is None:
                    #     print(f"❌ 获取章节信息失败: {title}")
                    #     error_count += 1
                    #     if error_count >= max_errors:
                    #         print("❌ 错误次数超过限制，停止同步")
                    #         break
                    #     continue
                    
                    # 获取划线列表
                    print(f"📝 获取划线列表...")
                    bookmark_list = get_bookmark_list(session,book_id)
                    if bookmark_list is None:
                        print(f"❌ 获取划线列表失败: {title}")
                        error_count += 1
                        if error_count >= max_errors:
                            print("❌ 错误次数超过限制，停止同步")
                            break
                        continue
                    
                    # 获取笔记和评论
                    print(f"💭 获取笔记和评论...")
                    summary, reviews = get_review_list(session,book_id)
                    # bookmark_list.extend(reviews)
                    
                    # 排序内容
                    bookmark_list = sorted(bookmark_list, key=lambda x: (
                        x.get("chapterUid", 1), 
                        0 if x.get("range", "") == "" else int(x.get("range").split("-")[0])
                    ))
                    
                    # 获取书籍详细信息
                    isbn, rating = get_bookinfo(session,book_id)
                    
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
                    page_id = insert_to_notion(title, book_id, book.get('cover', ''), latest_sort, 
                                            book.get('author', ''), isbn, rating, database_id, notion_token)
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