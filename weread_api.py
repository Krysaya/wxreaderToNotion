import os
import requests
import time
from datetime import datetime
from typing import List, Dict

class WeReadAPI:
    def __init__(self):
        self.session = requests.Session()
        self._setup_session()
        
        # 从环境变量获取完整的微信读书Cookie
        self.cookie_string = os.getenv('WEREAD_COOKIE')
        if not self.cookie_string:
            raise Exception("未设置 WEREAD_COOKIE 环境变量")
    
    def _setup_session(self):
        """设置请求头 - """
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': 'https://weread.qq.com/',
            'Origin': 'https://weread.qq.com',
        })
    
    def _set_cookies(self):
        """设置Cookie到session"""
        if self.cookie_string:
            # 解析Cookie字符串
            for cookie in self.cookie_string.split('; '):
                if '=' in cookie:
                    key, value = cookie.split('=', 1)
                    self.session.cookies.set(key.strip(), value.strip())
            return True
        return False
    
    def get_bookshelf(self) -> List[Dict]:
        """获取书架 - 使用正确的API接口"""
        if not self._set_cookies():
            return []
        
        try:
            # 正确的书架API接口 - 参考源码仓库
            url = "https://i.weread.qq.com/user/notebooks"
            print(f"📚 获取书架: {url}")
            
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                books = data.get('books', [])
                print(f"✅ 获取到 {len(books)} 本书")
                return books
            else:
                print(f"❌ 获取书架失败: {response.status_code}")
                print(f"响应: {response.text}")
                return []
                
        except Exception as e:
            print(f"❌ 请求失败: {e}")
            return []
    
    def get_book_highlights(self, book_id: str) -> List[Dict]:
        """获取书籍划线 - 使用正确的API接口"""
        if not self._set_cookies():
            return []
        
        try:
            # 正确的划线API接口 - 参考源码仓库
            url = "https://i.weread.qq.com/book/bookmarklist"
            params = {'bookId': book_id}
            
            print(f"📖 获取书籍划线: {book_id}")
            response = self.session.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                # 正确的数据结构 - 参考源码仓库
                highlights = data.get('updated', [])
                print(f"✅ 获取到 {len(highlights)} 条划线")
                return highlights
            else:
                print(f"❌ 获取划线失败: {response.status_code}")
                return []
                
        except Exception as e:
            print(f"❌ 请求失败: {e}")
            return []
    
    def test_connection(self) -> bool:
        """测试连接是否有效"""
        print("🧪 测试微信读书连接...")
        books = self.get_bookshelf()
        if books:
            print("✅ 微信读书连接成功")
            for i, book in enumerate(books[:3]):
                title = book.get('title', '未知')
                author = book.get('author', '未知作者')
                print(f"   {i+1}. {title} - {author}")
            return True
        else:
            print("❌ 微信读书连接失败")
            return False

class NotionClient:
    def __init__(self):
        self.token = os.getenv('NOTION_TOKEN')
        self.database_id = os.getenv('NOTION_DATABASE_ID')
        self.headers = {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json',
            'Notion-Version': '2022-06-28'
        }
    
    def create_page(self, highlight_data: Dict) -> bool:
        """在Notion中创建页面 - 参考源码仓库的数据结构"""
        url = 'https://api.notion.com/v1/pages'
        
        # 构建页面数据 - 使用正确的属性名
        data = {
            "parent": {"database_id": self.database_id},
            "properties": {
                "Name": {  # 使用Name作为标题
                    "title": [
                        {
                            "text": {
                                "content": highlight_data['book_title'][:200]
                            }
                        }
                    ]
                },
                "Book": {  # 书名属性
                    "rich_text": [
                        {
                            "text": {
                                "content": highlight_data['book_title'][:200]
                            }
                        }
                    ]
                },
                "Author": {  # 作者属性
                    "rich_text": [
                        {
                            "text": {
                                "content": highlight_data['author'][:200]
                            }
                        }
                    ]
                },
                "Chapter": {  # 章节属性
                    "rich_text": [
                        {
                            "text": {
                                "content": highlight_data['chapter'][:200]
                            }
                        }
                    ]
                },
                "Date": {  # 日期属性
                    "date": {
                        "start": highlight_data['date']
                    }
                }
            },
            "children": [
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {
                                    "content": "📖 划线内容："
                                },
                                "annotations": {
                                    "bold": True
                                }
                            }
                        ]
                    }
                },
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
        
        # 添加个人笔记（如果有）
        if highlight_data.get('note'):
            data["children"].extend([
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {
                                    "content": "💡 我的想法："
                                },
                                "annotations": {
                                    "bold": True
                                }
                            }
                        ]
                    }
                },
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {
                                    "content": highlight_data['note'][:1000]
                                }
                            }
                        ]
                    }
                }
            ])
        
        try:
            response = requests.post(url, headers=self.headers, json=data)
            if response.status_code == 200:
                return True
            else:
                print(f"❌ 创建Notion页面失败: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ 请求Notion API失败: {e}")
            return False

class WeReadToNotionSync:
    def __init__(self):
        self.weread = WeReadAPI()
        self.notion = NotionClient()
    
    def format_timestamp(self, timestamp: int) -> str:
        """格式化时间戳"""
        if timestamp == 0:
            return datetime.now().isoformat() + 'Z'
        try:
            dt = datetime.fromtimestamp(timestamp)
            return dt.isoformat() + 'Z'
        except:
            return datetime.now().isoformat() + 'Z'
    
    def sync(self):
        """同步划线到Notion"""
        print("🚀 开始同步微信读书笔记到Notion...")
        print("=" * 60)
        
        # 测试连接
        if not self.weread.test_connection():
            print("❌ 微信读书连接失败，停止同步")
            return
        
        # 获取书架
        books = self.weread.get_bookshelf()
        if not books:
            print("❌ 未获取到书籍，停止同步")
            return
        
        print(f"\n📚 处理前 3 本书...")
        
        total_highlights = 0
        success_count = 0
        
        # 处理每本书的划线
        for i, book in enumerate(books[:3]):
            book_id = book['bookId']
            book_title = book['title']
            book_author = book.get('author', '未知作者')
            
            print(f"\n📖 [{i+1}/3] 处理: {book_title}")
            
            # 获取划线笔记
            highlights = self.weread.get_book_highlights(book_id)
            
            for highlight in highlights:
                if highlight.get('markText'):
                    highlight_data = {
                        'book_title': book_title,
                        'author': book_author,
                        'chapter': highlight.get('chapterTitle', '未知章节'),
                        'highlight': highlight.get('markText', '').strip(),
                        'note': highlight.get('content', '').strip(),
                        'date': self.format_timestamp(highlight.get('createTime', 0))
                    }
                    
                    total_highlights += 1
                    print(f"  📝 同步划线: {highlight_data['highlight'][:50]}...")
                    
                    # 同步到Notion
                    if self.notion.create_page(highlight_data):
                        success_count += 1
                        print("    ✅ 同步成功")
                    else:
                        print("    ❌ 同步失败")
                    
                    time.sleep(0.5)
            
            time.sleep(1)
        
        # 输出总结
        print(f"\n🎉 同步完成!")
        print(f"📊 统计: 总划线 {total_highlights}, 成功 {success_count}, 失败 {total_highlights - success_count}")

def main():
    try:
        sync = WeReadToNotionSync()
        sync.sync()
    except Exception as e:
        print(f"💥 同步过程发生错误: {e}")

if __name__ == "__main__":
    main()