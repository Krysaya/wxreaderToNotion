import os
from cookiecloud_correct import CookieCloudClient

def main():
    print("🧪 测试正确的解密方法")
    print("=" * 50)
    
    server_url = os.getenv('COOKIECLOUD_SERVER')
    uuid = os.getenv('COOKIECLOUD_UUID') 
    password = os.getenv('COOKIECLOUD_PASSWORD')
    
    print(f"🔧 配置信息:")
    print(f"   服务器: {server_url}")
    print(f"   UUID: {uuid}")
    print(f"   密码: {'*' * len(password)}")
    
    if not all([server_url, uuid, password]):
        print("❌ 配置不完整")
        return
    
    client = CookieCloudClient(server_url, uuid, password)
    
    print("\n🔗 测试连接...")
    if client.test_connection():
        print("🎉 解密成功！")
    else:
        print("❌ 解密失败")
        print("\n💡 排查建议:")
        print("1. 确认密码与 CookieCloud 插件中设置的完全一致")
        print("2. 检查插件加密方式是否为 AES-128-CBC")
        print("3. 确认 IV 设置为 0x0")

if __name__ == "__main__":
    main()