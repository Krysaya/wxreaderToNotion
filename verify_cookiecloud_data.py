import os
import requests
import base64
import hashlib
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

def verify_data_storage():
    server_url = os.getenv('COOKIECLOUD_SERVER')
    uuid = os.getenv('COOKIECLOUD_UUID')
    
    print("🔍 验证 CookieCloud 数据存储")
    print("=" * 40)
    
    # 获取原始加密数据
    url = f"{server_url}/get/{uuid}"
    response = requests.get(url, timeout=30)
    
    if response.status_code == 200:
        data = response.json()
        encrypted_data = data.get('encrypted', '')
        
        print(f"✅ 服务器返回数据")
        print(f"📏 加密数据长度: {len(encrypted_data)}")
        print(f"🔐 有加密数据: {'是' if encrypted_data else '否'}")
        
        if encrypted_data:
            # 检查数据特征
            try:
                decoded = base64.b64decode(encrypted_data)
                print(f"📏 Base64解码后: {len(decoded)}字节")
                print(f"🎯 数据特征: 前10字节(hex) = {decoded[:10].hex()}")
                return True
            except:
                print("❌ 数据不是有效的Base64")
                return False
        else:
            print("❌ 服务器没有返回加密数据")
            return False
    else:
        print(f"❌ 服务器请求失败: {response.status_code}")
        return False

if __name__ == "__main__":
    success = verify_data_storage()
    print(f"\n{'✅ 数据存储正常' if success else '❌ 数据存储有问题'}")