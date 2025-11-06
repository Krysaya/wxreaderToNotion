import requests
import json
import base64
from typing import Dict, Optional
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.backends import default_backend
import os

class CookieCloudClient:
    def __init__(self, server_url: str, uuid: str, password: str):
        """
        初始化 CookieCloud 客户端 - 基于正确解密方法
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
            print(f"🔄 从 CookieCloud 获取数据...")
            
            # 发送请求
            response = requests.get(url, timeout=30)
            print(f"📡 响应状态码: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"📊 响应数据结构: {list(data.keys())}")
                
                # 新版 CookieCloud 使用 'encrypted' 字段
                if 'encrypted' in data:
                    encrypted_data = data['encrypted']
                    print(f"🔐 找到加密数据，长度: {len(encrypted_data)}")
                    
                    # 解密数据
                    decrypted_data = self._aes_decrypt(encrypted_data)
                    
                    if decrypted_data:
                        print("✅ 数据解密成功")
                        # 查找微信读书的 Cookie
                        return self._extract_weread_cookies(decrypted_data)
                    else:
                        print("❌ 数据解密失败")
                        return None
                else:
                    print("❌ 响应中没有 'encrypted' 字段")
                    return None
                    
            else:
                print(f"❌ 请求失败，状态码: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ 获取 Cookie 失败: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _aes_decrypt(self, encrypted_data: str) -> Optional[Dict]:
        """
        AES-256-CBC 解密 - 基于参考文章的正确方法
        """
        try:
            print("🔑 开始 AES-256-CBC 解密...")
            
            # 1. Base64 解码
            encrypted_bytes = base64.b64decode(encrypted_data)
            print(f"📏 Base64 解码后长度: {len(encrypted_bytes)} 字节")
            
            # 2. 生成密钥 (参考文章的方法)
            # 使用 UUID + 密码生成 32 字节密钥
            key_str = self.uuid + self.password
            # 使用 MD5 生成 32 字节密钥
            import hashlib
            key = hashlib.md5(key_str.encode()).hexdigest().encode()
            print(f"🔑 生成密钥: {key.hex()}")
            
            # 3. 提取 IV (前16字节) 和加密数据
            iv = encrypted_bytes[:16]
            ciphertext = encrypted_bytes[16:]
            print(f"🔑 IV: {iv.hex()}")
            print(f"📏 密文长度: {len(ciphertext)} 字节")
            
            # 4. 创建解密器
            backend = default_backend()
            cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=backend)
            decryptor = cipher.decryptor()
            
            # 5. 解密
            decrypted_padded = decryptor.update(ciphertext) + decryptor.finalize()
            
            # 6. 去除 PKCS7 填充
            unpadder = padding.PKCS7(128).unpadder()
            decrypted = unpadder.update(decrypted_padded) + unpadder.finalize()
            
            print(f"✅ 解密成功，数据长度: {len(decrypted)} 字节")
            
            # 7. 解析 JSON
            decrypted_str = decrypted.decode('utf-8')
            data = json.loads(decrypted_str)
            
            return data
            
        except Exception as e:
            print(f"❌ AES 解密失败: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _extract_weread_cookies(self, cookie_data: Dict) -> Optional[Dict]:
        """
        从 CookieCloud 数据中提取微信读书的 Cookie
        """
        try:
            print("🔍 提取微信读书 Cookie...")
            
            # CookieCloud 的数据结构
            cookies = cookie_data.get('cookie_data', {})
            print(f"📁 可用的域名: {list(cookies.keys())}")
            
            # 微信读书的域名
            weread_domains = [
                'weread.qq.com',
                '.weread.qq.com', 
                'i.weread.qq.com'
            ]
            
            weread_cookies = {}
            found_domains = []
            
            for domain in weread_domains:
                if domain in cookies:
                    found_domains.append(domain)
                    domain_cookies = cookies[domain]
                    
                    for path, cookie_dict in domain_cookies.items():
                        for cookie_name, cookie_value in cookie_dict.items():
                            weread_cookies[cookie_name] = cookie_value
            
            if weread_cookies:
                print(f"✅ 找到微信读书域名: {found_domains}")
                print(f"🍪 获取到 {len(weread_cookies)} 个 Cookie:")
                for cookie_name in weread_cookies.keys():
                    print(f"   - {cookie_name}")
                return weread_cookies
            else:
                print("❌ 未找到微信读书 Cookie")
                print("💡 请确保在 CookieCloud 插件中选择了微信读书域名")
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
            return cookies is not None and len(cookies) > 0
        except Exception as e:
            print(f"❌ 连接测试异常: {e}")
            return False