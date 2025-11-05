#!/usr/bin/env python3
"""
获取微信读书 refresh_token 的脚本
在本地运行这个脚本来获取token
"""

import os
import json
from weread import WeRead

def main():
    print("🦊 微信读书 Refresh Token 获取工具")
    print("=" * 50)
    
    # 初始化微信读书客户端
    weread = WeRead()
    
    print("1. 将会打开浏览器显示二维码")
    print("2. 请使用微信扫描二维码登录")
    print("3. 登录成功后会自动获取 refresh_token")
    print("=" * 50)
    
    try:
        # 二维码登录
        refresh_token = weread.login_via_qrcode()
        
        print("✅ 登录成功！")
        print("=" * 50)
        print(f"你的 WEREAD_REFRESH_TOKEN:")
        print(f"🔑 {refresh_token}")
        print("=" * 50)
        
        # 保存到文件（可选）
        with open('weread_token.txt', 'w') as f:
            f.write(refresh_token)
        print("📁 Token已保存到 weread_token.txt")
        
        # 测试token是否有效
        print("🧪 测试token有效性...")
        weread.set_refresh_token(refresh_token)
        books = weread.get_bookshelf()
        print(f"✅ Token有效！找到 {len(books)} 本书")
        
        print("\n🎯 下一步：")
        print("1. 将上面的 refresh_token 复制到 GitHub Secrets")
        print("2. 密钥名称: WEREAD_REFRESH_TOKEN")
        print("3. 值: 上面显示的token字符串")
        
    except Exception as e:
        print(f"❌ 获取token失败: {e}")
        print("请确保已安装 weread 库: pip install weread")

if __name__ == "__main__":
    main()