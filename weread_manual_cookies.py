import os
import requests
import time
from datetime import datetime
from typing import List, Dict

class WeReadManualCookies:
    def __init__(self):
        self.session = requests.Session()
        self._setup_session()
        
        # 从环境变量获取Cookie
        self.cookies = {
            'wr_fp': os.getenv('WEREAD_FP'),
            'wr_gid': os.getenv('WEREAD_GID'),
            'wr_rt': os.getenv('WEREAD_RT'),
            'wr_localvid': os.getenv('WEREAD_LOCALVID'),
            'wr_pf': os.getenv('WEREAD_PF'),
            'wr_skey': os.getenv('WEREAD_SKEY'),
            'wr_vid': os.getenv('WEREAD_VID'),
        }
    
    def _setup_session(self):
        """设置请求头"""
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': 'https://weread.qq.com/',
            'Origin': 'https://weread.qq.com',
            'Accept': 'application/json, text/plain, */*',
        })
    
    def _set_cookies(self):
        """设置Cookie到session"""
        print("🍪 设置Cookie...")
        for name, value in self.cookies.items():
            if value:
                self.session.cookies.set(name, value)
                print(f"   ✅ {name}: {value[:20]}{'...' if len(value) > 20 else ''}")
    
    def get_bookshelf(self) -> List[Dict]:
        """获取书架"""
        self._set_cookies()
        
        try:
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
                print(f"响应: {response.text[:200]}...")
                return []
                
        except Exception as e:
            print(f"❌ 请求失败: {e}")
            return []
    
    def get_book_highlights(self, book_id: str) -> List[Dict]:
        """获取书籍划线"""
        self._set_cookies()
        
        try:
            url = "https://i.weread.qq.com/book/bookmarklist"
            params = {'bookId': book_id}
            
            print(f"📖 获取书籍划线: {book_id}")
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
        """测试连接"""
        print("🧪 测试微信读书连接...")
        books = self.get_bookshelf()
        success = len(books) > 0
        if success:
            print("✅ 微信读书连接成功")
            for i, book in enumerate(books[:3]):
                print(f"   {i+1}. {book.get('title', '未知')} - {book.get('author', '未知作者')}")
        else:
            print("❌ 微信读书连接失败")
        return success