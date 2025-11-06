#!/usr/bin/env python3
"""
测试微信读书 API 连接
"""

import os
from weread_cookiecloud_aes128 import WeReadWithCookieCloud

def main():
    print("🧪 测试微信读书 API 连接")
    print("=" * 40)
    
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
        return False
    
    try:
        # 创建客户端
        client = WeReadWithCookieCloud(server_url, uuid, password)
        
        # 测试认证
        print("\n🔗 测试微信读书 API...")
        result = client.test_auth()
        
        if result:
            print("🎉 微信读书 API 测试成功!")
            return True
        else:
            print("❌ 微信读书 API 测试失败")
            return False
            
    except Exception as e:
        print(f"💥 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)