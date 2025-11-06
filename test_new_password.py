import os
import requests
import base64
import hashlib
import json
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

def test_new_password():
    server_url = os.getenv('COOKIECLOUD_SERVER')
    uuid = os.getenv('COOKIECLOUD_UUID')
    password = os.getenv('COOKIECLOUD_PASSWORD')
    
    print("🧪 测试新密码解密")
    print("=" * 40)
    print(f"密码MD5: {hashlib.md5(password.encode()).hexdigest()}")
    
    # 获取数据
    url = f"{server_url}/get/{uuid}"
    response = requests.get(url, timeout=30)
    data = response.json()
    encrypted_data = data['encrypted']
    
    # 解密
    encrypted_bytes = base64.b64decode(encrypted_data)
    key = hashlib.md5(password.encode()).digest()
    iv = b'\x00' * 16
    
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    decryptor = cipher.decryptor()
    decrypted = decryptor.update(encrypted_bytes) + decryptor.finalize()
    
    print(f"解密后数据长度: {len(decrypted)}字节")
    print(f"数据开头: {decrypted[:10]}")  # 显示前10字节
    
    # 检查是否是JSON
    if decrypted.startswith(b'{'):
        print("✅ 解密成功！数据是JSON格式")
        try:
            data_str = decrypted.decode('utf-8')
            json_data = json.loads(data_str)
            print(f"✅ JSON解析成功！键: {list(json_data.keys())}")
            return True
        except:
            print("❌ JSON解析失败")
    else:
        print("❌ 解密失败，数据不是JSON格式")
        print(f"数据开头(hex): {decrypted[:20].hex()}")
        return False

if __name__ == "__main__":
    success = test_new_password()
    print("🎉 测试成功!" if success else "💥 测试失败")