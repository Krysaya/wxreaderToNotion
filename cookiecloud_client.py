import requests
import json
import base64
from typing import Dict, Optional

class CookieCloudClient:
    def __init__(self, server_url: str, uuid: str, password: str):
        """
        初始化 CookieCloud 客户端
        
        Args:
            server_url: CookieCloud 服务器地址
            uuid: 你的设备 UUID
            password: 加密密码
        """
        self.server_url = server_url.rstrip('/')
        self.uuid = uuid
        self.password = password
        
    def get_cookies(self) -> Optional[Dict]:
        """
        从 CookieCloud 获取微信读书的 Cookie
        """
        try:
            # 构建请求 URL
            url = f"{self.server_url}/get/{self.uuid}"
            
            # 发送请求
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('status') == 'success':
                    # 解密数据
                    encrypted_data = data['data']
                    decrypted_data = self._decrypt_data(encrypted_data)
                    
                    if decrypted_data:
                        # 查找微信读书的 Cookie
                        return self._extract_weread_cookies(decrypted_data)
                    else:
                        print("❌ 数据解密失败")
                else:
                    print(f"❌ CookieCloud 返回错误: {data.get('message')}")
            else:
                print(f"❌ 请求失败，状态码: {response.status_code}")
                
        except Exception as e:
            print(f"❌ 获取 Cookie 失败: {e}")
            
        return None
    
    def _decrypt_data(self, encrypted_data: str) -> Optional[Dict]:
        """
        解密 CookieCloud 数据
        """
        try:
            # CookieCloud 使用 AES 加密，这里需要根据实际加密方式实现
            # 简化版本：假设数据是 base64 编码的 JSON
            decoded_data = base64.b64decode(encrypted_data)
            return json.loads(decoded_data)
        except:
            # 如果解密失败，尝试直接解析（某些配置可能不加密）
            try:
                return json.loads(encrypted_data)
            except:
                return None
    
    def _extract_weread_cookies(self, cookie_data: Dict) -> Optional[Dict]:
        """
        从 CookieCloud 数据中提取微信读书的 Cookie
        """
        try:
            # CookieCloud 的数据结构
            cookies = cookie_data.get('cookie_data', {})
            
            # 微信读书的域名
            weread_domains = [
                'weread.qq.com',
                '.weread.qq.com',
                'i.weread.qq.com'
            ]
            
            weread_cookies = {}
            
            for domain in weread_domains:
                if domain in cookies:
                    domain_cookies = cookies[domain]
                    for path, cookie_dict in domain_cookies.items():
                        for cookie_name, cookie_value in cookie_dict.items():
                            weread_cookies[cookie_name] = cookie_value
            
            if weread_cookies:
                print(f"✅ 获取到 {len(weread_cookies)} 个微信读书 Cookie")
                return weread_cookies
            else:
                print("❌ 未找到微信读书 Cookie")
                return None
                
        except Exception as e:
            print(f"❌ 提取 Cookie 失败: {e}")
            return None

    def test_connection(self) -> bool:
        """
        测试 CookieCloud 连接
        """
        try:
            cookies = self.get_cookies()
            return cookies is not None
        except:
            return False