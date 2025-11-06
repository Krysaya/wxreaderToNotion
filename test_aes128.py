import os
from cookiecloud_aes128 import CookieCloudClient

def main():
    print("🧪 测试 AES-128-CBC 解密")
    print("=" * 50)
    
    # 从环境变量获取配置
    server_url = os.getenv('COOKIECLOUD_SERVER')
    uuid = os.getenv('COOKIECLOUD_UUID') 
    password = os.getenv('COOKIECLOUD_PASSWORD')
    
    print(f"🔧 配置信息:")
    print(f"   服务器: {server_url}")
    print(f"   UUID: {uuid}")
    print(f"   密码: {'*' * len(password) if password else '未设置'}")
    
    if not all([server_url, uuid, password]):
        print("❌ 配置不完整")
        return
    
    # 创建客户端
    client = CookieCloudClient(server_url, uuid, password)
    
    # 测试连接
    print("\n🔗 测试 CookieCloud 连接...")
    success = client.test_connection()
    
    if success:
        print("\n🎉 AES-128-CBC 解密成功！")
        print("💡 现在可以更新主同步脚本使用这个客户端")
    else:
        print("\n❌ 解密仍然失败")
        print("💡 可能需要检查密码是否正确")

if __name__ == "__main__":
    main()