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
        """解密数据"""
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
            
            # 改进的填充处理
            pad_len = decrypted_padded[-1]
            if 0 < pad_len <= 16:
                # 验证填充是否正确
                padding = decrypted_padded[-pad_len:]
                if all(byte == pad_len for byte in padding):
                    decrypted = decrypted_padded[:-pad_len]
                    print(f"📏 去除{pad_len}字节PKCS7填充")
                else:
                    decrypted = decrypted_padded
                    print("⚠️ 填充验证失败，使用未去除填充的数据")
            else:
                decrypted = decrypted_padded
                print("⚠️ 未检测到标准填充")
            
            print(f"✅ 解密成功，数据长度: {len(decrypted)}字节")
            
            # 改进的JSON解析 - 按优先级尝试多种方式
            return self._parse_json_with_fallback(decrypted)
            
        except Exception as e:
            print(f"❌ 解密失败: {e}")
            import traceback
            traceback.print_exc()
            return None

    def _parse_json_with_fallback(self, data_bytes: bytes) -> Optional[Dict]:
        """改进的JSON解析，支持多种fallback方案"""
        
        # 方案1: 直接尝试UTF-8
        try:
            data_str = data_bytes.decode('utf-8')
            data = json.loads(data_str)
            print("✅ 使用UTF-8编码解析成功")
            return data
        except (UnicodeDecodeError, json.JSONDecodeError) as e:
            print(f"❌ UTF-8解析失败: {e}")
        
        # 方案2: 尝试UTF-8-sig (BOM)
        try:
            data_str = data_bytes.decode('utf-8-sig')
            data = json.loads(data_str)
            print("✅ 使用UTF-8-sig编码解析成功")
            return data
        except (UnicodeDecodeError, json.JSONDecodeError) as e:
            print(f"❌ UTF-8-sig解析失败: {e}")
        
        # 方案3: 尝试latin-1 (不会解码失败)
        try:
            data_str = data_bytes.decode('latin-1')
            data = json.loads(data_str)
            print("✅ 使用latin-1编码解析成功")
            return data
        except json.JSONDecodeError as e:
            print(f"❌ latin-1 JSON解析失败: {e}")
            # 显示数据开头帮助调试
            preview = data_str[:200] if len(data_str) > 200 else data_str
            print(f"🔍 数据预览: {repr(preview)}")
        
        # 方案4: 尝试去除BOM和其他不可见字符
        try:
            # 去除可能的BOM和特殊字符
            cleaned_bytes = data_bytes.lstrip(b'\xef\xbb\xbf\x00\x20\x09\x0a\x0d')
            data_str = cleaned_bytes.decode('utf-8', errors='ignore').strip()
            data = json.loads(data_str)
            print("✅ 使用清理后数据解析成功")
            return data
        except (UnicodeDecodeError, json.JSONDecodeError) as e:
            print(f"❌ 清理后数据解析失败: {e}")
        
        # 方案5: 显示原始数据帮助调试
        print("🔍 原始字节数据分析:")
        print(f"   前100字节: {data_bytes[:100]}")
        print(f"   前100字节(hex): {data_bytes[:100].hex()}")
        print(f"   数据开头字符: {chr(data_bytes[0]) if data_bytes else '空'}")
        
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