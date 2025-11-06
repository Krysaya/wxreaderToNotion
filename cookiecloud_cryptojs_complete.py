import requests
import base64
import hashlib
import json
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad
import os

class CookieCloudCryptoJS:
    def __init__(self, server_url: str, uuid: str, password: str):
        self.server_url = server_url.rstrip('/')
        self.uuid = uuid
        self.password = password
        
    def get_cookies(self):
        """获取Cookie - 完整的CryptoJS兼容方案"""
        try:
            print("🔄 从CookieCloud获取数据...")
            
            url = f"{self.server_url}/get/{self.uuid}"
            response = requests.get(url, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                
                if 'encrypted' in data:
                    encrypted_data = data['encrypted']
                    print(f"🔐 加密数据长度: {len(encrypted_data)}")
                    
                    # 尝试多种CryptoJS解密方法
                    decrypted_data = self._try_all_cryptojs_methods(encrypted_data)
                    
                    if decrypted_data:
                        print("✅ 数据解密成功")
                        return self._extract_weread_cookies(decrypted_data)
                    else:
                        print("❌ 所有CryptoJS解密方法失败")
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
    
    def _try_all_cryptojs_methods(self, encrypted_data: str):
        """尝试所有CryptoJS可能的解密方法"""
        methods = [
            self._decrypt_cryptojs_simple,      # 简单方法
            self._decrypt_cryptojs_evp,         # EVP密钥派生
            self._decrypt_cryptojs_no_salt,     # 无salt情况
        ]
        
        for i, method in enumerate(methods, 1):
            print(f"\n🔄 尝试CryptoJS方法 {i}...")
            try:
                result = method(encrypted_data)
                if result and 'cookie_data' in result:
                    print(f"✅ 方法 {i} 成功!")
                    return result
            except Exception as e:
                print(f"❌ 方法 {i} 失败: {e}")
                continue
                
        return None
    
    def _decrypt_cryptojs_simple(self, encrypted_data: str):
        """CryptoJS简单解密方法 - 最常见的配置"""
        try:
            # Base64解码
            encrypted_bytes = base64.b64decode(encrypted_data)
            print(f"   数据特征: 前16字节 = {encrypted_bytes[:16].hex()}")
            
            # CryptoJS默认使用MD5哈希字符串作为密码
            key_str = hashlib.md5(self.password.encode()).hexdigest()
            print(f"   密钥(MD5 hex): {key_str}")
            
            # 检查是否有Salted__前缀
            if encrypted_bytes.startswith(b'Salted__'):
                print("   🔍 检测到Salted__前缀，使用EVP密钥派生")
                return self._decrypt_with_evp(encrypted_bytes, key_str)
            else:
                print("   🔍 无Salted__前缀，使用简单密钥")
                return self._decrypt_with_simple_key(encrypted_bytes, key_str)
                
        except Exception as e:
            print(f"   简单方法失败: {e}")
            return None
    
    def _decrypt_cryptojs_evp(self, encrypted_data: str):
        """使用EVP_BytesToKey密钥派生"""
        try:
            encrypted_bytes = base64.b64decode(encrypted_data)
            
            # 即使没有Salted__也尝试EVP
            key_str = hashlib.md5(self.password.encode()).hexdigest()
            
            # 如果没有salt，创建一个空salt
            if encrypted_bytes.startswith(b'Salted__'):
                salt = encrypted_bytes[8:16]
                ciphertext = encrypted_bytes[16:]
            else:
                salt = b'\x00' * 8  # 空salt
                ciphertext = encrypted_bytes
            
            # EVP密钥派生
            key, iv = self._evp_bytes_to_key(key_str.encode(), salt, 32)
            print(f"   EVP派生密钥: {key.hex()}")
            print(f"   EVP派生IV: {iv.hex()}")
            
            # 解密
            cipher = AES.new(key, AES.MODE_CBC, iv)
            decrypted_padded = cipher.decrypt(ciphertext)
            decrypted = unpad(decrypted_padded, AES.block_size)
            
            data = json.loads(decrypted.decode('utf-8'))
            return data
            
        except Exception as e:
            print(f"   EVP方法失败: {e}")
            return None
    
    def _decrypt_cryptojs_no_salt(self, encrypted_data: str):
        """无salt的CryptoJS解密"""
        try:
            encrypted_bytes = base64.b64decode(encrypted_data)
            
            # 直接使用MD5摘要作为密钥
            key = hashlib.md5(self.password.encode()).digest()
            iv = b'\x00' * 16
            
            print(f"   无salt密钥: {key.hex()}")
            print(f"   无salt IV: {iv.hex()}")
            
            # 解密
            cipher = AES.new(key, AES.MODE_CBC, iv)
            decrypted_padded = cipher.decrypt(encrypted_bytes)
            decrypted = unpad(decrypted_padded, AES.block_size)
            
            data = json.loads(decrypted.decode('utf-8'))
            return data
            
        except Exception as e:
            print(f"   无salt方法失败: {e}")
            return None
    
    def _decrypt_with_evp(self, encrypted_bytes: bytes, key_str: str):
        """使用EVP_BytesToKey解密"""
        salt = encrypted_bytes[8:16]
        ciphertext = encrypted_bytes[16:]
        
        # EVP密钥派生
        key, iv = self._evp_bytes_to_key(key_str.encode(), salt, 32)
        
        # 解密
        cipher = AES.new(key, AES.MODE_CBC, iv)
        decrypted_padded = cipher.decrypt(ciphertext)
        decrypted = unpad(decrypted_padded, AES.block_size)
        
        data = json.loads(decrypted.decode('utf-8'))
        return data
    
    def _decrypt_with_simple_key(self, encrypted_bytes: bytes, key_str: str):
        """使用简单密钥解密"""
        # CryptoJS可能直接使用MD5字符串的前16字节
        key = key_str.encode('utf-8')[:16].ljust(16, b'\x00')
        iv = b'\x00' * 16
        
        # 解密
        cipher = AES.new(key, AES.MODE_CBC, iv)
        decrypted_padded = cipher.decrypt(encrypted_bytes)
        decrypted = unpad(decrypted_padded, AES.block_size)
        
        data = json.loads(decrypted.decode('utf-8'))
        return data
    
    def _evp_bytes_to_key(self, password: bytes, salt: bytes, key_len: int):
        """OpenSSL EVP_BytesToKey实现"""
        d = d_i = b''
        while len(d) < key_len:
            d_i = hashlib.md5(d_i + password + salt).digest()
            d += d_i
        return d[:16], d[16:32]  # 返回key和iv
    
    def _extract_weread_cookies(self, cookie_data):
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
                for name in weread_cookies.keys():
                    print(f"   🍪 {name}")
                return weread_cookies
            else:
                print("❌ 未找到微信读书Cookie")
                return None
                
        except Exception as e:
            print(f"❌ 提取Cookie失败: {e}")
            return None