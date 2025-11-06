import requests
import base64
import hashlib
import json

def analyze_data_format():
    server_url = "https://cc.chenge.ink"
    uuid = "1JJwasFJqKXDt53akmfP7z"
    password = "123456"
    
    print("🔍 深度分析数据格式")
    print("=" * 50)
    
    # 获取原始数据
    url = f"{server_url}/get/{uuid}"
    response = requests.get(url, timeout=30)
    data = response.json()
    encrypted_data = data['encrypted']
    
    print(f"加密数据长度: {len(encrypted_data)}")
    print(f"加密数据前50字符: {encrypted_data[:50]}")
    
    # Base64解码
    encrypted_bytes = base64.b64decode(encrypted_data)
    print(f"Base64解码后长度: {len(encrypted_bytes)}字节")
    print(f"数据开头(hex): {encrypted_bytes[:32].hex()}")
    print(f"数据结尾(hex): {encrypted_bytes[-16:].hex()}")
    
    # 分析数据特征
    print(f"\n📊 数据特征分析:")
    print(f"  数据长度: {len(encrypted_bytes)}字节")
    print(f"  长度模16: {len(encrypted_bytes) % 16} (应为0)")
    
    # 检查是否是有效的AES加密数据
    if len(encrypted_bytes) % 16 == 0:
        print("  ✅ 数据长度符合AES块大小")
    else:
        print("  ❌ 数据长度不符合AES块大小")
    
    # 检查可能的格式
    print(f"\n🔍 检查可能的数据格式:")
    
    # 1. 检查是否是双重Base64
    try:
        double_decoded = base64.b64decode(encrypted_bytes)
        print(f"  双重Base64解码长度: {len(double_decoded)}字节")
        if double_decoded.startswith(b'{'):
            print("  🎯 可能是双重Base64编码的JSON!")
    except:
        print("  不是双重Base64")
    
    # 2. 检查是否是未加密的JSON
    try:
        json_data = json.loads(encrypted_bytes)
        print("  🎯 数据是未加密的JSON!")
        return json_data
    except:
        print("  不是未加密JSON")
    
    # 3. 检查是否是其他编码
    try:
        as_text = encrypted_bytes.decode('utf-8')
        print(f"  可UTF-8解码为文本，长度: {len(as_text)}")
    except:
        print("  不是UTF-8文本")
    
    # 4. 显示数据统计信息
    print(f"\n📈 数据统计:")
    unique_bytes = len(set(encrypted_bytes))
    print(f"  唯一字节数: {unique_bytes}/256")
    print(f"  数据熵: {unique_bytes/256:.2%}")
    
    # 高熵通常表示加密数据，低熵可能表示压缩或编码数据
    if unique_bytes > 200:
        print("  📊 高熵数据 - 可能是加密数据")
    else:
        print("  📊 低熵数据 - 可能是编码或压缩数据")
    
    return None

if __name__ == "__main__":
    result = analyze_data_format()
    if result:
        print("\n🎉 发现数据格式!")
    else:
        print("\n🔍 需要进一步分析")