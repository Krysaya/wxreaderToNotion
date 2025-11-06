import requests
import base64
import hashlib
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad
import json

def test_nodejs_compatible():
    """模拟Node.js crypto.createCipher行为"""
    server_url = "https://cc.chenge.ink"
    uuid = "1JJwasFJqKXDt53akmfP7z"
    password = "123456"
    
    print("🔧 模拟Node.js crypto解密")
    print("=" * 40)
    
    # 获取数据
    url = f"{server_url}/get/{uuid}"
    response = requests.get(url, timeout=30)
    data = response.json()
    encrypted_data = data['encrypted']
    encrypted_bytes = base64.b64decode(encrypted_data)
    
    print(f"数据长度: {len(encrypted_bytes)}字节")
    
    # Node.js crypto.createCipher的密钥处理
    # 它内部会处理密钥派生，我们可能需要直接使用密码
    
    # 方法1: 直接使用密码作为密钥
    print(f"\n🔄 方法1: 直接使用密码")
    try:
        key = password.encode('utf-8').ljust(16, b'\x00')[:16]
        iv = b'\x00' * 16
        
        cipher = AES.new(key, AES.MODE_CBC, iv)
        decrypted = cipher.decrypt(encrypted_bytes)
        decrypted = unpad(decrypted, AES.block_size)
        
        data = json.loads(decrypted.decode('utf-8'))
        print("✅ 直接密码解密成功!")
        return data
    except Exception as e:
        print(f"❌ 失败: {e}")
    
    # 方法2: Node.js可能使用不同的密钥派生
    print(f"\n🔄 方法2: OpenSSL兼容密钥派生")
    try:
        # OpenSSL风格的密钥派生
        key = hashlib.md5(password.encode()).digest()
        iv = hashlib.md5(key + password.encode()).digest()[:16]
        
        cipher = AES.new(key, AES.MODE_CBC, iv)
        decrypted = cipher.decrypt(encrypted_bytes)
        decrypted = unpad(decrypted, AES.block_size)
        
        data = json.loads(decrypted.decode('utf-8'))
        print("✅ OpenSSL派生解密成功!")
        return data
    except Exception as e:
        print(f"❌ 失败: {e}")
    
    return None

if __name__ == "__main__":
    result = test_nodejs_compatible()
    if result:
        print("\n🎉 Node.js解密成功!")
    else:
        print("\n💥 Node.js解密失败")