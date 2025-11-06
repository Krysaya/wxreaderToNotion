import os
import requests
import base64
import hashlib
import json

def debug_raw_data():
    """分析原始加密数据"""
    server_url = os.getenv('COOKIECLOUD_SERVER')
    uuid = os.getenv('COOKIECLOUD_UUID')
    password = os.getenv('COOKIECLOUD_PASSWORD')
    
    print("🔍 分析原始加密数据")
    print("=" * 40)
    
    # 获取原始数据
    url = f"{server_url}/get/{uuid}"
    response = requests.get(url, timeout=30)
    raw_data = response.json()
    
    print(f"📊 原始响应键: {list(raw_data.keys())}")
    print(f"🔐 encrypted字段类型: {type(raw_data.get('encrypted'))}")
    print(f"🔐 encrypted字段长度: {len(raw_data.get('encrypted', ''))}")
    
    encrypted_data = raw_data['encrypted']
    
    # 检查是否是有效的Base64
    try:
        decoded = base64.b64decode(encrypted_data)
        print(f"✅ Base64有效，解码后长度: {len(decoded)}字节")
        print(f"🔍 解码数据前32字节(hex): {decoded[:32].hex()}")
    except:
        print("❌ 不是有效的Base64")
        return
    
    # 检查数据特征
    if encrypted_data.startswith('ey'):  # 'ey' 是 '{"' 的base64开头
        print("⚠️  数据可能已经是JSON格式")
        try:
            direct_json = json.loads(encrypted_data)
            print("✅ 直接解析为JSON成功!")
            return direct_json
        except:
            print("❌ 直接解析失败")
    
    # 显示密码信息
    print(f"🔑 密码长度: {len(password)}")
    print(f"🔑 密码MD5: {hashlib.md5(password.encode()).hexdigest()}")

if __name__ == "__main__":
    result = debug_raw_data()
    if result:
        print("🎉 发现数据格式!")