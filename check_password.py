import os
import hashlib

def main():
    password = os.getenv('COOKIECLOUD_PASSWORD', '')
    
    print("🔑 CookieCloud 密码检查")
    print("=" * 40)
    
    print(f"密码长度: {len(password)} 字符")
    print(f"密码MD5: {hashlib.md5(password.encode()).hexdigest()}")
    print(f"密码预览: {repr(password)}")
    
    print("\n💡 请在 CookieCloud 浏览器插件中检查：")
    print("1. 打开 CookieCloud 插件")
    print("2. 点击『设置』")
    print("3. 确认密码是否与上面显示的一致")
    print("4. 特别注意：空格、大小写、特殊字符")
    
    print("\n🔍 常见问题：")
    print("- 密码前后有空格")
    print("- 大小写不一致") 
    print("- 特殊字符编码问题")
    print("- 密码中包含不可见字符")

if __name__ == "__main__":
    main()