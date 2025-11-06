import requests
import json
import base64
import hashlib
from typing import Dict, Optional
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import os

class CookieCloudClient:
    def __init__(self, server_url: str, uuid: str, password: str):
        self.server_url = server_url.rstrip('/')
        self.uuid = uuid
        self.password = password
        
    def get_cookies(self) -> Optional[Dict]:
        """获取Cookie数据"""
        try:
            print("🔄 从CookieCloud获取数据...")
            
            url = f"{self.server_url}/get/{self.uuid}"
            response = requests.get(url, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ 获取到加密数据")
                
                if 'encrypted' in data:
                    encrypted_data = data['encrypted']
                    return self._decrypt_data(encrypted_data)
                else:
                    print("❌ 响应中没有encrypted字段")
                    return None
            else:
                print(f"❌ 请求失败: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ 获取数据失败: {e}")
            return None
    
    def _decrypt_data(self, encrypted_data: str) -> Optional[Dict]:
        """解密数据 - 基于MCP Server的实现"""
        try:
            print("🔐 开始解密数据...")
            
            # Base64解码
            encrypted_bytes = base64.b64decode(encrypted_data)
            print(f"📏 加密数据长度: {len(encrypted_bytes)}字节")
            
            # 生成密钥: MD5(密码)
            key = hashlib.md5(self.password.encode()).digest()
            print(f"🔑 密钥MD5: {key.hex()}")
            
            # AES-128-CBC解密，IV为16字节0
            iv = b'\x00' * 16
            cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
            decryptor = cipher.decryptor()
            
            # 解密
            decrypted_padded = decryptor.update(encrypted_bytes) + decryptor.finalize()
            
            # 去除PKCS7填充
            pad_len = decrypted_padded[-1]
            if 0 < pad_len <= 16:
                if all(b == pad_len for b in decrypted_padded[-pad_len:]):
                    decrypted = decrypted_padded[:-pad_len]
                else:
                    decrypted = decrypted_padded  # 填充验证失败，不去除
            else:
                decrypted = decrypted_padded
                print("⚠️ 使用未去除填充的数据")
            
            print(f"✅ 解密成功，数据长度: {len(decrypted)}字节")
            
            # 解析JSON 先尝试 latin-1（不会失败），再尝试 utf-8

            try:
                decrypted_str = decrypted.decode('latin-1')
                data = json.loads(decrypted_str)
            except:
                try:
                    decrypted_str = decrypted.decode('utf-8')
                    data = json.loads(decrypted_str)
                except:
                return None
            
            data = json.loads(decrypted_str)
            print(f"📄 解析出{len(data.get('cookie_data', {}))}个域名的Cookie")
            
            return data
            
        except Exception as e:
            print(f"❌ 解密失败: {e}")
            return None
    
    def get_weread_cookies(self) -> Optional[Dict]:
        """专门获取微信读书的Cookie"""
        cookie_data = self.get_cookies()
        if not cookie_data:
            return None
            
        try:
            cookies = cookie_data.get('cookie_data', {})
            weread_domains = ['weread.qq.com', '.weread.qq.com', 'i.weread.qq.com']
            
            weread_cookies = {}
            for domain in weread_domains:
                if domain in cookies:
                    for path, cookie_dict in cookies[domain].items():
                        weread_cookies.update(cookie_dict)
            
            if weread_cookies:
                print(f"✅ 获取到{len(weread_cookies)}个微信读书Cookie")
                return weread_cookies
            else:
                print("❌ 未找到微信读书Cookie")
                return None
                
        except Exception as e:
            print(f"❌ 提取微信读书Cookie失败: {e}")
            return None