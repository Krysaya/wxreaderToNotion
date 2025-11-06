import requests
import base64
import hashlib
import json
import zlib
import gzip

def ultimate_analysis():
    server_url = "https://cc.chenge.ink"
    uuid = "1JJwasFJqKXDt53akmfP7z"
    
    print("🔍 终极数据格式分析")
    print("=" * 50)
    
    # 获取原始数据
    url = f"{server_url}/get/{uuid}"
    response = requests.get(url, timeout=30)
    raw_response = response.text
    data = response.json()
    encrypted_data = data['encrypted']
    
    print(f"原始响应长度: {len(raw_response)}")
    print(f"encrypted字段长度: {len(encrypted_data)}")
    
    # 1. 检查是否是双重Base64
    print(f"\n1. 检查双重Base64...")
    try:
        first_decode = base64.b64decode(encrypted_data)
        second_decode = base64.b64decode(first_decode)
        if second_decode.startswith(b'{'):
            print("   ✅ 双重Base64发现JSON!")
            return json.loads(second_decode.decode('utf-8'))
        print(f"   双重解码长度: {len(second_decode)}")
    except:
        print("   不是双重Base64")
    
    # 2. 检查是否是压缩数据
    print(f"\n2. 检查压缩数据...")
    encrypted_bytes = base64.b64decode(encrypted_data)
    
    # GZIP压缩
    try:
        decompressed = gzip.decompress(encrypted_bytes)
        if decompressed.startswith(b'{'):
            print("   ✅ GZIP压缩的JSON!")
            return json.loads(decompressed.decode('utf-8'))
    except:
        pass
    
    # ZLIB压缩
    try:
        decompressed = zlib.decompress(encrypted_bytes)
        if decompressed.startswith(b'{'):
            print("   ✅ ZLIB压缩的JSON!")
            return json.loads(decompressed.decode('utf-8'))
    except:
        pass
    
    # 3. 检查是否是未加密但编码的数据
    print(f"\n3. 检查编码数据...")
    try:
        # 尝试直接作为JSON
        data = json.loads(encrypted_data)
        print("   ✅ 数据本身就是JSON!")
        return data
    except:
        print("   不是直接JSON")
    
    # 4. 详细分析字节数据
    print(f"\n4. 字节数据分析:")
    print(f"   数据长度: {len(encrypted_bytes)}字节")
    print(f"   数据开头(hex): {encrypted_bytes[:20].hex()}")
    print(f"   数据开头(ascii): {encrypted_bytes[:20]}")
    
    # 统计字节分布
    byte_counts = {}
    for byte in encrypted_bytes:
        byte_counts[byte] = byte_counts.get(byte, 0) + 1
    
    print(f"   唯一字节数: {len(byte_counts)}")
    print(f"   最常见字节: {sorted(byte_counts.items(), key=lambda x: x[1], reverse=True)[:5]}")
    
    # 5. 检查是否是其他加密算法
    print(f"\n5. 检查加密算法特征:")
    
    # 检查是否是流加密特征
    if len(set(encrypted_bytes)) > 250:
        print("   高熵 - 可能是加密数据")
    else:
        print("   低熵 - 可能是编码或弱加密")
    
    # 检查是否有明显的模式
    if encrypted_bytes[:8] == encrypted_bytes[8:16]:
        print("   检测到重复模式 - 可能是弱加密")
    else:
        print("   无重复模式 - 可能是强加密")
    
    # 6. 尝试无解密直接使用
    print(f"\n6. 尝试作为文本处理...")
    for encoding in ['utf-8', 'latin-1', 'ascii']:
        try:
            text = encrypted_bytes.decode(encoding)
            print(f"   可解码为{encoding}，长度: {len(text)}")
            if 'cookie' in text.lower():
                print(f"   🎯 包含'cookie'关键词!")
            if 'weread' in text.lower():
                print(f"   🎯 包含'weread'关键词!")
        except:
            print(f"   无法解码为{encoding}")
    
    return None

def check_server_implementation():
    """检查服务器实现"""
    print(f"\n🔧 检查服务器实现...")
    
    # 查看CookieCloud服务器源码中的加密实现
    print("根据CookieCloud源码分析:")
    print("  - 前端使用CryptoJS AES加密")
    print("  - 后端Node.js存储加密数据")
    print("  - 但实际数据可能因为版本差异而不同")
    
    print("\n💡 建议:")
    print("1. 检查CookieCloud插件版本")
    print("2. 查看插件设置中的加密选项")
    print("3. 尝试在插件中重新同步数据")
    print("4. 检查是否有特殊字符或编码问题")

if __name__ == "__main__":
    result = ultimate_analysis()
    if result:
        print(f"\n🎉 发现数据格式: {list(result.keys())}")
    else:
        print(f"\n🔍 无法确定数据格式")
        check_server_implementation()