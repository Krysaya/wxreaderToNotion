import requests
import json
import base64
import hashlib
from typing import Dict, Optional
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import os

class CookieCloudNodeJSFixed:
    def __init__(self, server_url: str, uuid: str, password: str):
        self.server_url = server_url.rstrip('/')
        self.uuid = uuid
        self.password = password
        
    def get_cookies(self) -> Optional[Dict]:
        """获取Cookie - 修复Node.js兼容性"""
        try:
            print("🔄 从CookieCloud获取数据...")
            
            url = f"{self.server_url}/get/{self.uuid}"
            response = requests.get(url, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                
                if 'encrypted' in data:
                    encrypted_data = data['encrypted']
                    print(f"🔐 加密数据长度: {len(encrypted_data)}")
                    
                    # 使用修复的解密方法
                    decrypted_data = self._decrypt_nodejs_compatible(encrypted_data)
                    
                    if decrypted_data:
                        print("✅ 数据解密成功")
                        return self._extract_weread_cookies(decrypted_data)
                    else:
                        print("❌ 数据解密失败")
                        return None
                else:
                    print("❌ 响应中没有encrypted字段")
                    return None
                    
            else:
                print(f"❌ 请求失败: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ 获取数据失败: {e}")
            return None
    
    def _decrypt_nodejs_compatible(self, encrypted_data: str) -> Optional[Dict]:
        """Node.js兼容解密方法"""
        try:
            # Base64解码
            encrypted_bytes = base64.b64decode(encrypted_data)
            print(f"📏 Base64解码后长度: {len(encrypted_bytes)}字节")
            
            # 关键修复：使用Node.js方式的密钥生成
            # Node.js: MD5哈希的十六进制字符串作为密钥
            key_hex = hashlib.md5(self.password.encode()).hexdigest()
            key = key_hex.encode('utf-8')  # 32字节的十六进制字符串
            print(f"🔑 密钥(hex): {key_hex}")
            print(f"🔑 密钥长度: {len(key)}字节")
            
            # Node.js的createCipher使用固定的IV
            # 根据Node.js文档，IV通常是全零
            iv = b'\x00' * 16
            
            # 解密
            cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
            decryptor = cipher.decryptor()
            decrypted = decryptor.update(encrypted_bytes) + decryptor.finalize()
            
            print(f"✅ 解密成功，数据长度: {len(decrypted)}字节")
            print(f"🔍 数据开头: {decrypted[:10].hex()}")
            
            # 解析JSON
            try:
                data_str = decrypted.decode('utf-8')
                data = json.loads(data_str)
                print("✅ JSON解析成功")
                return data
            except (UnicodeDecodeError, json.JSONDecodeError) as e:
                print(f"❌ JSON解析失败: {e}")
                # 显示数据开头帮助调试
                print(f"🔍 数据预览: {decrypted[:100]}")
                return None
                
        except Exception as e:
            print(f"❌ 解密失败: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _extract_weread_cookies(self, cookie_data: Dict) -> Optional[Dict]:
        """提取微信读书Cookie"""
        try:
            cookies = cookie_data.get('cookie_data', {})
            print(f"📁 可用域名: {list(cookies.keys())}")
            
            weread_domains = ['weread.qq.com', '.weread.qq.com', 'i.weread.qq.com']
            weread_cookies = {}
            
            for domain in weread_domains:
                if domain in cookies:
                    for path, cookie_dict in cookies[domain].items():
                        weread_cookies.update(cookie_dict)
            
            if weread_cookies:
                print(f"✅ 找到{len(weread_cookies)}个微信读书Cookie")
                return weread_cookies
            else:
                print("❌ 未找到微信读书Cookie")
                return None
                
        except Exception as e:
            print(f"❌ 提取Cookie失败: {e}")
            return None