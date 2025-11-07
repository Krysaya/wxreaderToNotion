import os
import requests
import time
from datetime import datetime
from typing import List, Dict

class WeReadAPI:
    def __init__(self):
        self.session = requests.Session()
        self._setup_session()
        
        # 从环境变量获取完整的微信读书Cookie字符串
        self.cookie_string = os.getenv('WEREAD_TOKEN')
        if not self.cookie_string:
            raise Exception("未设置 WEREAD_COOKIE 环境变量")
    
    def _setup_session(self):
        """设置请求头"""
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': 'https://weread.qq.com/',
            'Origin': 'https://weread.qq.com',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        })
    
    def _set_cookies(self):
        """设置完整的Cookie字符串到session"""
        if self.cookie_string:
            # 将Cookie字符串解析并设置到session
            cookies_dict = {}
            for cookie in self.cookie_string.split('; '):
                if '=' in cookie:
                    key, value = cookie.split('=', 1)
                    cookies_dict[key.strip()] = value.strip()
                    self.session.cookies.set(key.strip(), value.strip())
            
            print(f"🍪 已设置 {len(cookies_dict)} 个Cookie")
            return True
        return False
    
    def get_bookshelf(self) -> List[Dict]:
        """获取书架"""
        if not self._set_cookies():
            return []
        
        try:
            url = "https://i.weread.qq.com/user/notebooks"
            print(f"📚 获取书架...")
            
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                books = data.get('books', [])
                print(f"✅ 获取到 {len(books)} 本书")
                return books
            else:
                print(f"❌ 获取书架失败: {response.status_code}")
                print(f"响应: {response.text[:200]}")
                return []
                
        except Exception as e:
            print(f"❌ 请求失败: {e}")
            return []
    
    def get_book_highlights(self, book_id: str) -> List[Dict]:
        """获取书籍划线笔记"""
        if not self._set_cookies():
            return []
        
        try:
            url = "https://i.weread.qq.com/book/bookmarklist"
            params = {'bookId': book_id}
            
            print(f"📖 获取书籍 {book_id} 的划线...")
            response = self.session.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
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
            # 显示前3本书
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
        
        if not self.token or not self.database_id:
            raise Exception("请设置 NOTION_TOKEN 和 NOTION_DATABASE_ID 环境变量")
    
    def create_highlight_page(self, highlight_data: Dict) -> bool:
        """在Notion中创建划线笔记页面"""
        url = 'https://api.notion.com/v1/pages'
        
        # 构建页面数据
        data = {
            "parent": {"database_id": self.database_id},
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
                                "content": highlight_data['author'][:200]
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
                        "start": highlight_data['date']
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
        
        # 添加个人笔记（如果有）
        if highlight_data.get('note'):
            data["children"].append({
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
                                "bold": True,
                                "color": "blue"
                            }
                        }
                    ]
                }
            })
            data["children"].append({
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
            })
        
        try:
            response = requests.post(url, headers=self.headers, json=data)
            if response.status_code == 200:
                return True
            else:
                print(f"❌ 创建Notion页面失败: {response.status_code}")
                print(f"错误信息: {response.text}")
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
            # 微信读书的时间戳是秒级
            dt = datetime.fromtimestamp(timestamp)
            return dt.isoformat() + 'Z'
        except:
            return datetime.now().isoformat() + 'Z'
    
    def sync_highlights(self, limit_books: int = 3):
        """同步划线笔记到Notion"""
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
        
        print(f"\n📚 处理前 {limit_books} 本书...")
        
        total_highlights = 0
        success_count = 0
        
        # 处理每本书的划线
        for i, book in enumerate(books[:limit_books]):
            book_id = book['bookId']
            book_title = book['title']
            book_author = book.get('author', '未知作者')
            
            print(f"\n📖 [{i+1}/{min(len(books), limit_books)}] 处理: {book_title}")
            
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
                    if self.notion.create_highlight_page(highlight_data):
                        success_count += 1
                        print("    ✅ 同步成功")
                    else:
                        print("    ❌ 同步失败")
                    
                    # 避免请求过快
                    time.sleep(0.5)
            
            # 书籍间间隔
            time.sleep(1)
        
        # 输出总结
        print(f"\n🎉 同步完成!")
        print(f"📊 统计:")
        print(f"   总划线数: {total_highlights}")
        print(f"   成功同步: {success_count}")
        print(f"   失败: {total_highlights - success_count}")

def main():
    """主函数"""
    try:
        sync = WeReadToNotionSync()
        sync.sync_highlights(limit_books=3)  # 每次同步前3本书
        
    except Exception as e:
        print(f"💥 同步过程发生错误: {e}")
        exit(1)

if __name__ == "__main__":
    main()