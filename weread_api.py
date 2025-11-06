import requests
import time
from typing import List, Dict, Optional
from cookiecloud_final import CookieCloudClient

class WeReadAPI:
    def __init__(self, cookiecloud_server: str, cookiecloud_uuid: str, cookiecloud_password: str):
        self.cookie_client = CookieCloudClient(cookiecloud_server, cookiecloud_uuid, cookiecloud_password)
        self.session = requests.Session()
        self._setup_session()
    
    def _setup_session(self):
        """设置请求头"""
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': 'https://weread.qq.com/',
            'Origin': 'https://weread.qq.com',
        })
    
    def _refresh_cookies(self) -> bool:
        """刷新Cookie"""
        cookies = self.cookie_client.get_weread_cookies()
        if not cookies:
            return False
            
        # 清空现有cookies
        self.session.cookies.clear()
        
        # 设置新cookies
        for name, value in cookies.items():
            self.session.cookies.set(name, value)
        
        print("✅ Cookie刷新成功")
        return True
    
    def get_bookshelf(self) -> List[Dict]:
        """获取书架"""
        if not self._refresh_cookies():
            return []
            
        try:
            url = "https://i.weread.qq.com/user/notebooks"
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                books = data.get('books', [])
                print(f"✅ 获取到{len(books)}本书")
                return books
            else:
                print(f"❌ 获取书架失败: {response.status_code}")
                return []
                
        except Exception as e:
            print(f"❌ 请求失败: {e}")
            return []
    
    def get_book_highlights(self, book_id: str) -> List[Dict]:
        """获取书籍划线"""
        if not self._refresh_cookies():
            return []
            
        try:
            url = "https://i.weread.qq.com/book/bookmarklist"
            params = {'bookId': book_id}
            
            response = self.session.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                highlights = data.get('updated', [])
                print(f"✅ 获取到{len(highlights)}条划线")
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
        return len(books) > 0