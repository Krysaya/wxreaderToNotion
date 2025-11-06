import os
import requests
import time
from datetime import datetime
from weread_with_cookiecloud import WeReadWithCookieCloud

class WeReadToNotionWithCookieCloud:
    def __init__(self):
        # CookieCloud 配置（从环境变量获取）
        self.cookiecloud_server = os.getenv('COOKIECLOUD_SERVER')
        self.cookiecloud_uuid = os.getenv('COOKIECLOUD_UUID') 
        self.cookiecloud_password = os.getenv('COOKIECLOUD_PASSWORD')
        
        # Notion 配置
        self.notion_token = os.getenv('NOTION_TOKEN')
        self.notion_database_id = os.getenv('NOTION_DATABASE_ID')
        
        self.notion_headers = {
            'Authorization': f'Bearer {self.notion_token}',
            'Content-Type': 'application/json',
            'Notion-Version': '2022-06-28'
        }
        
        # 初始化客户端
        self.weread_client = WeReadWithCookieCloud(
            self.cookiecloud_server,
            self.cookiecloud_uuid, 
            self.cookiecloud_password
        )
    
    def check_config(self):
        """检查配置"""
        required_env_vars = {
            'COOKIECLOUD_SERVER': self.cookiecloud_server,
            'COOKIECLOUD_UUID': self.cookiecloud_uuid,
            'COOKIECLOUD_PASSWORD': self.cookiecloud_password,
            'NOTION_TOKEN': self.notion_token,
            'NOTION_DATABASE_ID': self.notion_database_id
        }
        
        missing_vars = [name for name, value in required_env_vars.items() if not value]
        if missing_vars:
            print(f"❌ 缺少环境变量: {', '.join(missing_vars)}")
            return False
        return True
    
    def get_weread_data(self):
        """获取微信读书数据"""
        print("📚 开始获取微信读书数据...")
        
        # 测试认证
        if not self.weread_client.test_auth():
            print("❌ 微信读书认证失败")
            return []
        
        try:
            books = self.weread_client.get_bookshelf()
            all_highlights = []
            
            for i, book in enumerate(books[:5]):  # 限制处理前5本书
                book_id = book['bookId']
                book_title = book['title']
                book_author = book.get('author', '未知作者')
                
                print(f"📖 处理第 {i+1}/{len(books)} 本: {book_title}")
                
                highlights = self.weread_client.get_bookmark_list(book_id)
                
                for highlight in highlights:
                    if highlight.get('markText'):
                        highlight_data = {
                            'book_title': book_title,
                            'book_author': book_author,
                            'book_cover': book.get('cover', ''),
                            'highlight': highlight.get('markText', '').strip(),
                            'chapter': highlight.get('chapterTitle', '未知章节'),
                            'create_time': self.format_time(highlight.get('createTime', 0)),
                            'note': highlight.get('content', '').strip()
                        }
                        all_highlights.append(highlight_data)
                
                print(f"  ✅ 找到 {len(highlights)} 条划线")
                time.sleep(1)  # 避免请求过快
            
            print(f"🎯 总共获取到 {len(all_highlights)} 条划线")
            return all_highlights
            
        except Exception as e:
            print(f"❌ 获取数据失败: {e}")
            return []
    
    def format_time(self, timestamp):
        """格式化时间"""
        if timestamp == 0:
            return datetime.now().isoformat() + 'Z'
        try:
            dt = datetime.fromtimestamp(timestamp)
            return dt.isoformat() + 'Z'
        except:
            return datetime.now().isoformat() + 'Z'
    
    def create_notion_page(self, highlight_data):
        """创建 Notion 页面（与之前相同）"""
        # ... 使用之前相同的 Notion 创建逻辑
            url = 'https://api.notion.com/v1/pages'
        
        data = {
            "parent": {"database_id": self.notion_database_id},
            "properties": {
                "书名": {
                    "title": [
                        {
                            "text": {
                                "content": highlight_data['book_title'][:200]
                            }
                        }
                    ]
                },
                "作者": {
                    "rich_text": [
                        {
                            "text": {
                                "content": highlight_data['book_author'][:200]
                            }
                        }
                    ]
                },
                "章节": {
                    "rich_text": [
                        {
                            "text": {
                                "content": highlight_data['chapter'][:200]
                            }
                        }
                    ]
                },
                "日期": {
                    "date": {
                        "start": highlight_data['create_time']
                    }
                }
            },
            "children": [
                {
                    "object": "block",
                    "type": "quote",
                    "quote": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {
                                    "content": highlight_data['highlight'][:2000]
                                }
                            }
                        ]
                    }
                }
            ]
        }
        
        if highlight_data.get('note'):
            data["children"].append({
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {
                                "content": f"📝 笔记：{highlight_data['note'][:1000]}"
                            }
                        }
                    ]
                }
            })
        
        try:
            response = requests.post(url, headers=self.notion_headers, json=data)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"❌ 创建Notion页面失败: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"响应内容: {e.response.text}")
            return None
        pass
    
    def sync(self):
        """执行同步"""
        print("🚀 开始 CookieCloud 同步...")
        
        if not self.check_config():
            return
        
        highlights = self.get_weread_data()
        
        if not highlights:
            print("❌ 未获取到数据")
            return
        
        # 同步到 Notion（使用之前的同步逻辑）
        success_count = 0
        for i, highlight in enumerate(highlights, 1):
            print(f"🔄 同步第 {i}/{len(highlights)} 条")
            result = self.create_notion_page(highlight)
            if result:
                success_count += 1
            time.sleep(0.3)
        
        print(f"🎉 同步完成！成功 {success_count}/{len(highlights)} 条")

if __name__ == "__main__":
    sync = WeReadToNotionWithCookieCloud()
    sync.sync()