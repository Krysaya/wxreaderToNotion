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
        初始化 CookieCloud 客户端 - AES-128-CBC 固定 IV
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
                    
                    # 使用正确的 AES-128-CBC 解密
                    decrypted_data = self._aes128_decrypt(encrypted_data)
                    
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
    
    def _aes128_decrypt(self, encrypted_data: str) -> Optional[Dict]:
        """
        AES-128-CBC 解密 - 固定 IV 为 0x0
        """
        try:
            print("🔑 开始 AES-128-CBC 解密...")
            print("⚙️  配置: AES-128-CBC, IV=0x0")
            
            # 1. Base64 解码
            encrypted_bytes = base64.b64decode(encrypted_data)
            print(f"📏 Base64 解码后长度: {len(encrypted_bytes)} 字节")
            
            # 2. 生成 16 字节密钥 (AES-128 需要 16 字节密钥)
            # 方法: MD5(密码) 取前16字节
            key_md5 = hashlib.md5(self.password.encode()).digest()  # 16字节
            print(f"🔑 生成密钥(MD5): {key_md5.hex()}")
            
            # 3. 固定 IV 为 16 字节的 0
            iv = b'\x00' * 16
            print(f"🔑 固定 IV: {iv.hex()}")
            
            # 4. 整个数据都是密文（没有单独的IV部分）
            ciphertext = encrypted_bytes
            print(f"📏 密文长度: {len(ciphertext)} 字节")
            
            # 5. 创建解密器
            backend = default_backend()
            cipher = Cipher(algorithms.AES(key_md5), modes.CBC(iv), backend=backend)
            decryptor = cipher.decryptor()
            
            # 6. 解密
            decrypted_padded = decryptor.update(ciphertext) + decryptor.finalize()
            
            # 7. 去除 PKCS7 填充
            # 查找最后一个字节的值作为填充长度
            pad_len = decrypted_padded[-1]
            if pad_len > 0 and pad_len <= 16:
                decrypted = decrypted_padded[:-pad_len]
                print(f"📏 去除 {pad_len} 字节填充")
            else:
                # 如果没有标准填充，直接使用
                decrypted = decrypted_padded
                print("⚠️  未检测到标准填充")
            
            print(f"✅ 解密成功，数据长度: {len(decrypted)} 字节")
            
            # 8. 解析 JSON
            decrypted_str = decrypted.decode('utf-8')
            data = json.loads(decrypted_str)
            
            print(f"📄 解密数据键: {list(data.keys())}")
            return data
            
        except Exception as e:
            print(f"❌ AES-128-CBC 解密失败: {e}")
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
                'i.weread.qq.com',
                'www.weread.qq.com'
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
                    cookie_value = weread_cookies[cookie_name]
                    print(f"   - {cookie_name}: {cookie_value[:30]}{'...' if len(cookie_value) > 30 else ''}")
                return weread_cookies
            else:
                print("❌ 未找到微信读书 Cookie")
                # 显示所有可用的域名和 Cookie 数量
                for domain, paths in cookies.items():
                    total_cookies = sum(len(cookie_dict) for cookie_dict in paths.values())
                    print(f"   {domain}: {total_cookies} 个 Cookie")
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
            success = cookies is not None and len(cookies) > 0
            if success:
                print(f"🎉 CookieCloud 连接测试成功，获取到 {len(cookies)} 个 Cookie")
            else:
                print("❌ CookieCloud 连接测试失败")
            return success
        except Exception as e:
            print(f"❌ 连接测试异常: {e}")
            return False