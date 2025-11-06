import requests
import json
import time
from cookiecloud_client import CookieCloudClient

class WeReadWithCookieCloud:
    def __init__(self, cookiecloud_server: str, cookiecloud_uuid: str, cookiecloud_password: str):
        """
        使用 CookieCloud 的微信读书客户端
        """
        self.cookiecloud = CookieCloudClient(cookiecloud_server, cookiecloud_uuid, cookiecloud_password)
        self.session = requests.Session()
        self._setup_session()
    
    def _setup_session(self):
        """设置会话头部"""
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': 'https://weread.qq.com/',
            'Origin': 'https://weread.qq.com',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        })
    
    def refresh_cookies(self) -> bool:
        """从 CookieCloud 刷新 Cookie"""
        try:
            cookies = self.cookiecloud.get_cookies()
            if cookies:
                # 清空现有 Cookie
                self.session.cookies.clear()
                
                # 添加新的 Cookie
                for name, value in cookies.items():
                    self.session.cookies.set(name, value)
                
                print("✅ Cookie 刷新成功")
                return True
            else:
                print("❌ 无法获取 Cookie")
                return False
        except Exception as e:
            print(f"❌ 刷新 Cookie 失败: {e}")
            return False
    
    def get_bookshelf(self):
        """获取书架"""
        # 先刷新 Cookie
        if not self.refresh_cookies():
            return []
        
        try:
            url = "https://i.weread.qq.com/user/notebooks"
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                books = data.get('books', [])
                print(f"✅ 获取到 {len(books)} 本书")
                return books
            else:
                print(f"❌ 获取书架失败: {response.status_code}")
                return []
                
        except Exception as e:
            print(f"❌ 请求失败: {e}")
            return []
    
    def get_bookmark_list(self, book_id: str):
        """获取书籍划线"""
        if not self.refresh_cookies():
            return []
        
        try:
            url = f"https://i.weread.qq.com/book/bookmarklist"
            params = {'bookId': book_id}
            
            response = self.session.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                bookmarks = data.get('updated', [])
                print(f"✅ 获取到 {len(bookmarks)} 条划线")
                return bookmarks
            else:
                print(f"❌ 获取划线失败: {response.status_code}")
                return []
                
        except Exception as e:
            print(f"❌ 请求失败: {e}")
            return []
    
    def test_auth(self) -> bool:
        """测试认证是否有效"""
        books = self.get_bookshelf()
        return len(books) > 0