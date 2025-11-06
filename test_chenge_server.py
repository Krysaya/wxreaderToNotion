import os
from cookiecloud_cryptojs_complete import CookieCloudCryptoJS

def main():
    # 使用你的测试配置
    server_url = "https://cc.chenge.ink"
    uuid = "1JJwasFJqKXDt53akmfP7z"
    password = "123456"
    
    print("🧪 完整CryptoJS兼容测试")
    print("=" * 50)
    
    client = CookieCloudCryptoJS(server_url, uuid, password)
    cookies = client.get_cookies()
    
    if cookies:
        print(f"\n🎉 解密成功! 获取到 {len(cookies)} 个Cookie")
    else:
        print(f"\n💥 解密失败")

if __name__ == "__main__":
    main()