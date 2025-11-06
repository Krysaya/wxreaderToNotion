import os
import requests
import base64
import hashlib
import json
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

def debug_decrypt():
    server_url = os.getenv('COOKIECLOUD_SERVER')
    uuid = os.getenv('COOKIECLOUD_UUID')
    password = os.getenv('COOKIECLOUD_PASSWORD')
    
    print("🔍 解密诊断")
    print("=" * 40)
    
    # 获取数据
    url = f"{server_url}/get/{uuid}"
    response = requests.get(url, timeout=30)
    data = response.json()
    encrypted_data = data['encrypted']
    
    print(f"加密数据长度: {len(encrypted_data)}")
    print(f"密码: {'*' * len(password)}")
    print(f"密钥MD5: {hashlib.md5(password.encode()).hexdigest()}")
    
    # 解密
    encrypted_bytes = base64.b64decode(encrypted_data)
    key = hashlib.md5(password.encode()).digest()
    iv = b'\x00' * 16
    
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    decryptor = cipher.decryptor()
    decrypted = decryptor.update(encrypted_bytes) + decryptor.finalize()
    
    print(f"解密后长度: {len(decrypted)}字节")
    
    # 分析数据
    print(f"前100字节: {decrypted[:100]}")
    print(f"前100字节(hex): {decrypted[:100].hex()}")
    
    # 检查是否是双重加密
    try:
        # 尝试再次解密
        cipher2 = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
        decryptor2 = cipher2.decryptor()
        double_decrypted = decryptor2.update(decrypted) + decryptor2.finalize()
        print(f"双重解密后长度: {len(double_decrypted)}字节")
        print(f"双重解密前100字节: {double_decrypted[:100]}")
    except:
        print("双重解密失败")
    
    # 检查数据特征
    if decrypted.startswith(b'{'):
        print("✅ 数据以{开头，应该是JSON")
    else:
        print("❌ 数据不以{开头，可能不是JSON")

if __name__ == "__main__":
    debug_decrypt()