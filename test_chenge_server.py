import requests
import base64
import hashlib
import json
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

def test_chenge_server():
    # 你的配置
    server_url = "https://cc.chenge.ink"
    uuid = "1JJwasFJqKXDt53akmfP7z"
    password = "123456"
    
    print("🧪 测试陈哥服务器解密")
    print("=" * 40)
    print(f"服务器: {server_url}")
    print(f"UUID: {uuid}")
    print(f"密码: {password}")
    print(f"密码MD5: {hashlib.md5(password.encode()).hexdigest()}")
    
    # 获取数据
    url = f"{server_url}/get/{uuid}"
    print(f"\n📡 请求URL: {url}")
    
    try:
        response = requests.get(url, timeout=30)
        print(f"响应状态: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"响应键: {list(data.keys())}")
            
            if 'encrypted' in data:
                encrypted_data = data['encrypted']
                print(f"\n🔐 加密数据长度: {len(encrypted_data)}")
                
                # 尝试多种解密方法
                methods = [
                    ("方法1: MD5摘要16字节", hashlib.md5(password.encode()).digest()),
                    ("方法2: MD5十六进制32字节", hashlib.md5(password.encode()).hexdigest().encode('utf-8')),
                ]
                
                for method_name, key in methods:
                    print(f"\n🔄 尝试{method_name}...")
                    result = try_decrypt(encrypted_data, key, method_name)
                    if result:
                        return result
                
                print("\n❌ 所有方法都失败")
                return None
            else:
                print("❌ 响应中没有encrypted字段")
                return None
        else:
            print(f"❌ 请求失败: {response.status_code}")
            print(f"响应内容: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ 请求异常: {e}")
        return None

def try_decrypt(encrypted_data: str, key: bytes, method_name: str):
    """尝试解密"""
    try:
        # Base64解码
        encrypted_bytes = base64.b64decode(encrypted_data)
        print(f"   Base64解码后: {len(encrypted_bytes)}字节")
        
        # 固定IV
        iv = b'\x00' * 16
        
        # 解密
        cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
        decryptor = cipher.decryptor()
        decrypted_padded = decryptor.update(encrypted_bytes) + decryptor.finalize()
        
        # 去除填充
        pad_len = decrypted_padded[-1]
        if 0 < pad_len <= 16:
            decrypted = decrypted_padded[:-pad_len]
            print(f"   去除{pad_len}字节填充")
        else:
            decrypted = decrypted_padded
            print("   未检测到标准填充")
        
        print(f"   解密后长度: {len(decrypted)}字节")
        print(f"   数据开头(hex): {decrypted[:20].hex()}")
        
        # 检查是否是JSON
        if decrypted.startswith(b'{'):
            print("   🎯 数据是JSON格式!")
            try:
                data_str = decrypted.decode('utf-8')
                data = json.loads(data_str)
                print("   ✅ JSON解析成功!")
                print(f"   数据键: {list(data.keys())}")
                if 'cookie_data' in data:
                    domains = list(data['cookie_data'].keys())
                    print(f"   🍪 找到Cookie域名: {domains}")
                return data
            except Exception as e:
                print(f"   ❌ JSON解析失败: {e}")
        else:
            print(f"   ❌ 数据不是JSON，开头字符: {chr(decrypted[0])}")
            
        return None
        
    except Exception as e:
        print(f"   ❌ 解密失败: {e}")
        return None

if __name__ == "__main__":
    result = test_chenge_server()
    if result:
        print("\n🎉 测试成功! 找到正确的解密方法")
    else:
        print("\n💥 测试失败")