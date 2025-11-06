import os
from weread_with_cookiecloud_fixed import WeReadWithCookieCloud

def main():
    print("🧪 测试修复后的 CookieCloud 集成")
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
    client = WeReadWithCookieCloud(server_url, uuid, password)
    
    # 测试连接
    print("\n🔗 测试 CookieCloud 连接...")
    if client.refresh_cookies():
        print("✅ CookieCloud 连接成功")
        
        # 测试微信读书 API
        print("\n📚 测试微信读书 API...")
        if client.test_auth():
            print("🎉 所有测试通过！")
            
            # 获取一些数据作为演示
            books = client.get_bookshelf()
            if books:
                print(f"\n📖 前3本书:")
                for i, book in enumerate(books[:3]):
                    print(f"   {i+1}. {book.get('title', '未知')} - {book.get('author', '未知作者')}")
        else:
            print("❌ 微信读书 API 测试失败")
    else:
        print("❌ CookieCloud 连接失败")

if __name__ == "__main__":
    main()