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
        """
        初始化 CookieCloud 客户端 - 使用正确的密钥生成方式
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
                
                if 'encrypted' in data:
                    encrypted_data = data['encrypted']
                    print(f"🔐 找到加密数据，长度: {len(encrypted_data)}")
                    
                    # 使用正确的解密方法
                    decrypted_data = self._correct_decrypt(encrypted_data)
                    
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
    
    def _correct_decrypt(self, encrypted_data: str) -> Optional[Dict]:
        """
        正确的解密方法 - 基于 CookieCloud 官方实现
        """
        try:
            print("🔑 使用正确的解密方法...")
            
            # 1. Base64 解码
            encrypted_bytes = base64.b64decode(encrypted_data)
            print(f"📏 Base64 解码后长度: {len(encrypted_bytes)} 字节")
            
            # 2. 生成密钥 - 正确的做法: MD5(密码)
            key = hashlib.md5(self.password.encode()).digest()
            print(f"🔑 生成密钥(MD5): {key.hex()}")
            
            # 3. 固定 IV 为 16 字节的 0
            iv = b'\x00' * 16
            print(f"🔑 固定 IV: {iv.hex()}")
            
            # 4. 解密
            cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
            decryptor = cipher.decryptor()
            decrypted_padded = decryptor.update(encrypted_bytes) + decryptor.finalize()
            
            # 5. 去除 PKCS7 填充
            pad_len = decrypted_padded[-1]
            if 0 < pad_len <= 16:
                # 验证填充是否正确
                if all(byte == pad_len for byte in decrypted_padded[-pad_len:]):
                    decrypted = decrypted_padded[:-pad_len]
                    print(f"📏 去除 {pad_len} 字节填充")
                else:
                    print("⚠️  填充验证失败，尝试不去除填充")
                    decrypted = decrypted_padded
            else:
                decrypted = decrypted_padded
                print("⚠️  未检测到标准填充")
            
            print(f"✅ 解密成功，数据长度: {len(decrypted)} 字节")
            
            # 6. 解析 JSON - 尝试多种编码
            return self._parse_json_safely(decrypted)
            
        except Exception as e:
            print(f"❌ 解密失败: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _parse_json_safely(self, data_bytes: bytes) -> Optional[Dict]:
        """
        安全地解析 JSON，尝试多种编码
        """
        encodings = ['utf-8', 'utf-8-sig', 'latin-1', 'iso-8859-1']
        
        for encoding in encodings:
            try:
                print(f"🔄 尝试 {encoding} 编码...")
                data_str = data_bytes.decode(encoding)
                result = json.loads(data_str)
                print(f"✅ 使用 {encoding} 编码解析成功")
                return result
            except (UnicodeDecodeError, json.JSONDecodeError) as e:
                print(f"❌ {encoding} 失败: {e}")
                continue
        
        # 如果所有编码都失败，显示原始数据帮助调试
        print("🔍 原始数据前100字节:", data_bytes[:100])
        print("🔍 原始数据hex:", data_bytes[:100].hex())
        return None
    
    def _extract_weread_cookies(self, cookie_data: Dict) -> Optional[Dict]:
        """
        从 CookieCloud 数据中提取微信读书的 Cookie
        """
        try:
            print("🔍 提取微信读书 Cookie...")
            
            cookies = cookie_data.get('cookie_data', {})
            print(f"📁 可用的域名: {list(cookies.keys())}")
            
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
                print(f"✅ 找到 {len(weread_cookies)} 个微信读书 Cookie")
                for name in weread_cookies.keys():
                    print(f"   🍪 {name}")
                return weread_cookies
            else:
                print("❌ 未找到微信读书 Cookie")
                return None
                
        except Exception as e:
            print(f"❌ 提取 Cookie 失败: {e}")
            return None

    def test_connection(self) -> bool:
        """测试连接"""
        cookies = self.get_cookies()
        return cookies is not None