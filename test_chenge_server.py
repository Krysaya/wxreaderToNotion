import requests
import base64
import hashlib
import json
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

def extended_test():
    server_url = "https://cc.chenge.ink"
    uuid = "1JJwasFJqKXDt53akmfP7z"
    password = "123456"
    
    print("🔍 扩展解密测试")
    print("=" * 40)
    
    # 获取数据
    url = f"{server_url}/get/{uuid}"
    response = requests.get(url, timeout=30)
    data = response.json()
    encrypted_data = data['encrypted']
    
    print(f"加密数据: {encrypted_data[:100]}...")
    
    # 尝试更多解密方法
    methods = [
        # 方法1: 直接使用密码作为密钥（如果密码是16字节）
        ("直接密码16字节", password.encode('utf-8') if len(password) == 16 else None),
        
        # 方法2: 密码填充到16字节
        ("密码填充16字节", password.encode('utf-8').ljust(16, b'\x00')[:16]),
        
        # 方法3: MD5摘要
        ("MD5摘要16字节", hashlib.md5(password.encode()).digest()),
        
        # 方法4: MD5十六进制
        ("MD5十六进制32字节", hashlib.md5(password.encode()).hexdigest().encode('utf-8')),
        
        # 方法5: SHA256前16字节
        ("SHA256前16字节", hashlib.sha256(password.encode()).digest()[:16]),
        
        # 方法6: 尝试无解密（数据可能未加密）
        ("无解密", None),
    ]
    
    for method_name, key in methods:
        if key is None and method_name == "无解密":
            print(f"\n🔄 尝试无解密...")
            # 直接尝试解析为JSON
            try:
                data = json.loads(encrypted_data)
                print("   ✅ 直接JSON解析成功!")
                return data
            except:
                print("   ❌ 直接JSON解析失败")
            continue
            
        if key is None:
            continue
            
        print(f"\n🔄 尝试{method_name}...")
        result = try_decrypt_method(encrypted_data, key, method_name)
        if result:
            return result
    
    # 最后尝试：数据可能是双重Base64编码
    print(f"\n🔄 尝试双重Base64解码...")
    try:
        decoded_once = base64.b64decode(encrypted_data)
        decoded_twice = base64.b64decode(decoded_once)
        data_str = decoded_twice.decode('utf-8')
        data = json.loads(data_str)
        print("✅ 双重Base64解码成功!")
        return data
    except:
        print("❌ 双重Base64解码失败")
    
    print("\n❌ 所有方法都失败")
    return None

def try_decrypt_method(encrypted_data: str, key: bytes, method_name: str):
    """尝试解密方法"""
    try:
        encrypted_bytes = base64.b64decode(encrypted_data)
        
        # 如果密钥长度不是16、24、32字节，跳过
        if len(key) not in [16, 24, 32]:
            print(f"   跳过: 密钥长度{len(key)}不支持")
            return None
            
        iv = b'\x00' * 16
        
        # 根据密钥长度选择AES版本
        if len(key) == 16:
            algorithm = algorithms.AES(key)
        elif len(key) == 24:
            algorithm = algorithms.AES(key)
        elif len(key) == 32:
            algorithm = algorithms.AES(key)
        
        cipher = Cipher(algorithm, modes.CBC(iv), backend=default_backend())
        decryptor = cipher.decryptor()
        decrypted = decryptor.update(encrypted_bytes) + decryptor.finalize()
        
        print(f"   解密后: {len(decrypted)}字节, 开头: {decrypted[:10].hex()}")
        
        # 尝试解析JSON
        for encoding in ['utf-8', 'latin-1']:
            try:
                data_str = decrypted.decode(encoding)
                data = json.loads(data_str)
                print(f"   ✅ 使用{encoding}编码解析成功!")
                return data
            except:
                continue
                
        return None
        
    except Exception as e:
        print(f"   ❌ 失败: {e}")
        return None

if __name__ == "__main__":
    result = extended_test()
    if result:
        print("\n🎉 找到正确的解密方法!")
        print(f"数据键: {list(result.keys())}")
    else:
        print("\n💥 所有解密方法都失败")
        print("可能的原因:")
        print("1. 密码不正确")
        print("2. 加密算法不是AES-128-CBC")
        print("3. IV不是全零")
        print("4. 数据格式不是JSON")