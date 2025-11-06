import os
from weread_manual_cookies import WeReadManualCookies

def main():
    print("🧪 测试手动Cookie方案")
    print("=" * 40)
    
    client = WeReadManualCookies()
    
    if client.test_connection():
        print("\n🎉 手动Cookie方案成功!")
    else:
        print("\n❌ 手动Cookie方案失败")

if __name__ == "__main__":
    main()
    