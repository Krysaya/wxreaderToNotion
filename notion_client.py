import requests
import os
from datetime import datetime
from typing import Dict

class NotionClient:
    def __init__(self):
        self.token = os.getenv('NOTION_TOKEN')
        self.database_id = os.getenv('NOTION_DATABASE_ID')
        self.headers = {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json',
            'Notion-Version': '2022-06-28'
        }
    
    def create_highlight_page(self, highlight_data: Dict) -> bool:
        """在Notion中创建划线页面"""
        url = 'https://api.notion.com/v1/pages'
        
        data = {
            "parent": {"database_id": self.database_id},
            "properties": {
                "书名": {
                    "title": [
                        {"text": {"content": highlight_data['book_title'][:200]}}
                    ]
                },
                "作者": {
                    "rich_text": [
                        {"text": {"content": highlight_data['author'][:200]}}
                    ]
                },
                "章节": {
                    "rich_text": [
                        {"text": {"content": highlight_data['chapter'][:200]}}
                    ]
                },
                "日期": {
                    "date": {"start": highlight_data['date']}
                }
            },
            "children": [
                {
                    "object": "block",
                    "type": "quote",
                    "quote": {
                        "rich_text": [
                            {"type": "text", "text": {"content": highlight_data['highlight'][:2000]}}
                        ]
                    }
                }
            ]
        }
        
        # 添加笔记
        if highlight_data.get('note'):
            data["children"].append({
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [
                        {"type": "text", "text": {"content": f"笔记：{highlight_data['note'][:1000]}"}}
                    ]
                }
            })
        
        try:
            response = requests.post(url, headers=self.headers, json=data)
            return response.status_code == 200
        except:
            return False