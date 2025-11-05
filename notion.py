import os
import requests
import json
import time
from datetime import datetime

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
    
    def get_weread_data(self):
        """
        获取微信读书数据
        注意：这里需要你后续配置真实的微信读书API
        """
        print("正在获取微信读书数据...")
        
        # 模拟数据 - 用于测试
        mock_highlights = [
            {
                'book_title': '示例书籍1',
                'book_author': '作者A',
                'book_cover': '',
                'highlight': '这是第一段划线内容，测试同步功能。',
                'chapter': '第一章 开始',
                'create_time': '2024-01-15T10:00:00Z',
                'note': '这个观点很有启发'
            },
            {
                'book_title': '示例书籍2', 
                'book_author': '作者B',
                'book_cover': '',
                'highlight': '这是另一段重要的划线内容。',
                'chapter': '第三节 深入理解',
                'create_time': '2024-01-16T14:30:00Z',
                'note': ''
            }
        ]
        
        print(f"获取到 {len(mock_highlights)} 条示例数据")
        return mock_highlights
    
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
                                "content": highlight_data['book_title']
                            }
                        }
                    ]
                },
                "作者": {
                    "rich_text": [
                        {
                            "text": {
                                "content": highlight_data['book_author']
                            }
                        }
                    ]
                },
                "章节": {
                    "rich_text": [
                        {
                            "text": {
                                "content": highlight_data['chapter']
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
                                    "content": highlight_data['highlight']
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
                                "content": f"笔记：{highlight_data['note']}"
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
            print(f"创建Notion页面失败: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"响应内容: {e.response.text}")
            return None
    
    def sync(self):
        """执行同步"""
        print("开始同步微信读书数据到Notion...")
        print(f"Notion数据库ID: {self.notion_database_id}")
        
        # 检查环境变量
        if not all([self.notion_token, self.notion_database_id]):
            print("错误：请先配置 Notion 相关的环境变量")
            return
        
        # 获取数据
        highlights = self.get_weread_data()
        print(f"获取到 {len(highlights)} 条划线笔记")
        
        # 同步到Notion
        success_count = 0
        for i, highlight in enumerate(highlights, 1):
            print(f"正在同步第 {i}/{len(highlights)} 条: {highlight['book_title']}")
            result = self.create_notion_page(highlight)
            if result and 'id' in result:
                success_count += 1
                print(f"✓ 成功同步")
            else:
                print(f"✗ 同步失败")
            time.sleep(0.5)  # 避免请求过于频繁
        
        print(f"同步完成！成功创建 {success_count}/{len(highlights)} 条记录")

if __name__ == "__main__":
    sync = WeReadToNotionSync()
    sync.sync()