import os
import requests
import json
import time
from datetime import datetime

try:
    from weread import WeRead
except ImportError:
    print("❌ 未安装 weread 库，请运行: pip install weread")
    exit(1)

class WeReadToNotionSync:
    def __init__(self):
        self.weread_refresh_token = os.getenv('WEREAD_REFRESH_TOKEN')
        self.notion_token = os.getenv('NOTION_TOKEN')
        self.notion_database_id = os.getenv('NOTION_DATABASE_ID')
        
        self.notion_headers = {
            'Authorization': f'Bearer {self.notion_token}',
            'Content-Type': 'application/json',
            'Notion-Version': '2022-06-28'
        }
        
        # 初始化微信读书客户端
        self.weread_client = WeRead()
    
    def setup_weread_auth(self):
        """设置微信读书认证"""
        if self.weread_refresh_token and self.weread_refresh_token != "your_weread_refresh_token_here":
            print(f"🔑 使用已有的 refresh_token: {self.weread_refresh_token[:10]}...")
            try:
                self.weread_client.set_refresh_token(self.weread_refresh_token)
                # 测试token是否有效
                books = self.weread_client.get_bookshelf()
                print(f"✅ Token有效，找到 {len(books)} 本书")
                return True
            except Exception as e:
                print(f"❌ Token无效: {e}")
                return False
        else:
            print("❌ 未找到有效的 WEREAD_REFRESH_TOKEN")
            return False
    
    def get_weread_data(self):
        """获取微信读书数据"""
        print("📚 开始获取微信读书数据...")
        
        try:
            # 获取书架书籍
            books = self.weread_client.get_bookshelf()
            print(f"找到 {len(books)} 本书")
            
            all_highlights = []
            
            for i, book in enumerate(books, 1):
                book_id = book['bookId']
                book_title = book['title']
                book_author = book.get('author', '未知作者')
                
                print(f"📖 处理第 {i}/{len(books)} 本: {book_title}")
                
                try:
                    # 获取书籍的划线笔记
                    highlights = self.weread_client.get_bookmark_list(book_id)
                    
                    for highlight in highlights:
                        highlight_data = {
                            'book_title': book_title,
                            'book_author': book_author,
                            'book_cover': book.get('cover', ''),
                            'highlight': highlight.get('markText', '').strip(),
                            'chapter': highlight.get('chapterTitle', '未知章节'),
                            'create_time': self.format_time(highlight.get('createTime', 0)),
                            'note': highlight.get('content', '').strip()
                        }
                        
                        # 只添加有实际内容的划线
                        if highlight_data['highlight']:
                            all_highlights.append(highlight_data)
                    
                    print(f"  ✅ 找到 {len(highlights)} 条划线")
                    time.sleep(0.5)  # 避免请求过快
                    
                except Exception as e:
                    print(f"  ❌ 获取书籍划线失败: {e}")
                    continue
            
            print(f"🎯 总共获取到 {len(all_highlights)} 条有效划线")
            return all_highlights
            
        except Exception as e:
            print(f"❌ 获取微信读书数据失败: {e}")
            return []
    
    def format_time(self, timestamp):
        """格式化时间戳"""
        if timestamp == 0:
            return datetime.now().isoformat() + 'Z'
        try:
            # 微信读书的时间戳通常是秒级
            dt = datetime.fromtimestamp(timestamp)
            return dt.isoformat() + 'Z'
        except:
            return datetime.now().isoformat() + 'Z'
    
    def create_notion_page(self, highlight_data):
        """在Notion中创建页面"""
        url = 'https://api.notion.com/v1/pages'
        
        data = {
            "parent": {"database_id": self.notion_database_id},
            "properties": {
                "书名": {
                    "title": [
                        {
                            "text": {
                                "content": highlight_data['book_title'][:200]  # Notion标题长度限制
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
                                    "content": highlight_data['highlight'][:2000]  # 限制长度
                                }
                            }
                        ]
                    }
                }
            ]
        }
        
        # 添加笔记（如果有）
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
            return None
    
    def sync(self):
        """执行同步"""
        print("🚀 开始同步微信读书数据到Notion...")
        
        # 检查Notion配置
        if not all([self.notion_token, self.notion_database_id]):
            print("❌ 请先配置 NOTION_TOKEN 和 NOTION_DATABASE_ID")
            return
        
        # 设置微信读书认证
        if not self.setup_weread_auth():
            print("❌ 微信读书认证失败，请检查 WEREAD_REFRESH_TOKEN")
            return
        
        # 获取数据
        highlights = self.get_weread_data()
        if not highlights:
            print("❌ 未获取到任何划线数据")
            return
        
        # 同步到Notion
        success_count = 0
        print(f"🔄 开始同步 {len(highlights)} 条划线到Notion...")
        
        for i, highlight in enumerate(highlights, 1):
            print(f"📤 同步第 {i}/{len(highlights)} 条: {highlight['book_title']}")
            result = self.create_notion_page(highlight)
            if result and 'id' in result:
                success_count += 1
                print("  ✅ 同步成功")
            else:
                print("  ❌ 同步失败")
            time.sleep(0.3)  # 避免请求过快
        
        print(f"🎉 同步完成！成功创建 {success_count}/{len(highlights)} 条记录")

if __name__ == "__main__":
    sync = WeReadToNotionSync()
    sync.sync()