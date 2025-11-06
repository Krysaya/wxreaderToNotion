import os
import base64
import hashlib
import json
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import requests

def debug_decrypted_data():
    """
    调试解密后的数据
    """
    server_url = os.getenv('COOKIECLOUD_SERVER')
    uuid = os.getenv('COOKIECLOUD_UUID')
    password = os.getenv('COOKIECLOUD_PASSWORD')
    
    print("🔍 调试解密数据")
    print("=" * 50)
    
    # 获取加密数据
    url = f"{server_url}/get/{uuid}"
    response = requests.get(url, timeout=30)
    data = response.json()
    encrypted_data = data['encrypted']
    
    print(f"📏 加密数据长度: {len(encrypted_data)}")
    
    # 解密
    encrypted_bytes = base64.b64decode(encrypted_data)
    key_md5 = hashlib.md5(password.encode()).digest()
    iv = b'\x00' * 16
    
    cipher = Cipher(algorithms.AES(key_md5), modes.CBC(iv), backend=default_backend())
    decryptor = cipher.decryptor()
    decrypted_padded = decryptor.update(encrypted_bytes) + decryptor.finalize()
    
    # 去除填充
    pad_len = decrypted_padded[-1]
    if pad_len > 0 and pad_len <= 16:
        decrypted = decrypted_padded[:-pad_len]
    else:
        decrypted = decrypted_padded
    
    print(f"✅ 解密成功，数据长度: {len(decrypted)} 字节")
    
    # 分析数据
    print(f"🔍 数据前100字节: {decrypted[:100]}")
    print(f"🔍 数据hex: {decrypted[:100].hex()}")
    
    # 尝试各种编码
    encodings = ['utf-8', 'utf-8-sig', 'latin-1', 'iso-8859-1', 'cp1252']
    
    for encoding in encodings:
        try:
            decoded = decrypted.decode(encoding)
            print(f"\n✅ {encoding} 解码成功")
            print(f"📄 前200字符: {decoded[:200]}")
            
            # 尝试解析JSON
            try:
                json_data = json.loads(decoded)
                print(f"🎯 JSON解析成功! 键: {list(json_data.keys())}")
                return json_data
            except json.JSONDecodeError as e:
                print(f"❌ JSON解析失败: {e}")
                
        except UnicodeDecodeError as e:
            print(f"❌ {encoding} 解码失败: {e}")
    
    print("\n❌ 所有编码方式都失败")
    return None

if __name__ == "__main__":
    result = debug_decrypted_data()
    if result:
        print("\n🎉 调试成功!")
    else:
        print("\n💥 调试失败")