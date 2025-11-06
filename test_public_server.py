import requests
import json

def test_public_server():
    """测试公共 CookieCloud 服务器"""
    
    # 公共演示服务器（仅用于测试）
    public_servers = [
        "https://cookiecloud.moonbegonia.com",
        "https://cookiecloud.mcpp.cc"
    ]
    
    # 测试用的公开 UUID（这些是演示用的）
    test_uuids = [
        "demo",  # 有些公共服务器提供演示端点
        "test"
    ]
    
    for server in public_servers:
        print(f"\n🔗 测试公共服务器: {server}")
        print("=" * 50)
        
        for uuid in test_uuids:
            test_url = f"{server}/get/{uuid}"
            print(f"\n🆔 测试 UUID: {uuid}")
            print(f"📡 请求 URL: {test_url}")
            
            try:
                response = requests.get(test_url, timeout=10)
                print(f"✅ 状态码: {response.status_code}")
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        print(f"📊 响应键: {list(data.keys())}")
                        if 'status' in data:
                            print(f"🎯 Status: {data['status']}")
                            if data['status'] == 'success':
                                print("✨ 这个服务器工作正常！")
                                print(f"💡 建议使用: {server}")
                                return server
                        else:
                            print("❌ 没有 status 字段")
                    except json.JSONDecodeError:
                        print("❌ 响应不是 JSON")
                else:
                    print(f"❌ HTTP 错误: {response.status_code}")
                    
            except Exception as e:
                print(f"💥 错误: {e}")
    
    print("\n❌ 所有公共服务器测试失败")
    return None

if __name__ == "__main__":
    working_server = test_public_server()
    if working_server:
        print(f"\n🎉 找到可用的服务器: {working_server}")
        print(f"💡 请在你的 GitHub Secrets 中更新 COOKIECLOUD_SERVER 为: {working_server}")