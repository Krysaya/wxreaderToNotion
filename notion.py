import requests
import json
import time

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
