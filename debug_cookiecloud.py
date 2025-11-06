import os
import requests
import json
import base64

def debug_cookiecloud():
    # 从环境变量获取配置
    server_url = os.getenv('COOKIECLOUD_SERVER')
    uuid = os.getenv('COOKIECLOUD_UUID')
    password = os.getenv('COOKIECLOUD_PASSWORD')
    
    print("🔍 CookieCloud 调试诊断")
    print("=" * 50)
    
    # 1. 检查环境变量
    print("1. 检查环境变量:")
    print(f"   SERVER: {'✅ 已设置' if server_url else '❌ 未设置'} - {server_url}")
    print(f"   UUID: {'✅ 已设置' if uuid else '❌ 未设置'} - {uuid}")
    print(f"   PASSWORD: {'✅ 已设置' if password else '❌ 未设置'} - {'*' * len(password) if password else ''}")
    
    if not all([server_url, uuid, password]):
        print("❌ 环境变量不完整")
        return
    
    # 2. 测试服务器连接
    print("\n2. 测试服务器连接:")
    test_url = f"{server_url.rstrip('/')}/get/{uuid}"
    print(f"   请求URL: {test_url}")
    
    try:
        response = requests.get(test_url, timeout=10)
        print(f"   响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            # 尝试解析响应
            try:
                data = response.json()
                print(f"   响应JSON: {json.dumps(data, ensure_ascii=False, indent=2)}")
                
                # 分析响应
                if 'status' in data:
                    if data['status'] == 'success':
                        print("   ✅ 服务器返回成功状态")
                        # 检查数据
                        encrypted_data = data.get('data', '')
                        if encrypted_data:
                            print(f"   加密数据长度: {len(encrypted_data)}")
                            
                            # 尝试解密
                            try:
                                # 先尝试 base64 解码
                                decoded = base64.b64decode(encrypted_data)
                                print(f"   Base64解码后长度: {len(decoded)}")
                                
                                # 尝试 JSON 解析
                                try:
                                    decrypted = json.loads(decoded)
                                    print("   ✅ 数据解密成功")
                                    print(f"   解密数据结构: {list(decrypted.keys()) if decrypted else '空'}")
                                    
                                    # 检查微信读书 Cookie
                                    if 'cookie_data' in decrypted:
                                        cookie_data = decrypted['cookie_data']
                                        weread_found = False
                                        for domain in ['weread.qq.com', '.weread.qq.com', 'i.weread.qq.com']:
                                            if domain in cookie_data:
                                                weread_found = True
                                                cookies = cookie_data[domain]
                                                print(f"   ✅ 找到微信读书域名: {domain}")
                                                for path, cookie_dict in cookies.items():
                                                    print(f"      路径: {path}, Cookie数量: {len(cookie_dict)}")
                                                    for cookie_name in cookie_dict.keys():
                                                        print(f"        - {cookie_name}")
                                        if not weread_found:
                                            print("   ❌ 未找到微信读书 Cookie")
                                    
                                except json.JSONDecodeError:
                                    print("   ❌ 解密后的数据不是有效的 JSON")
                                    print(f"   解密数据预览: {decoded[:100]}...")
                                    
                            except Exception as e:
                                print(f"   ❌ Base64解码失败: {e}")
                        else:
                            print("   ❌ 响应中没有数据字段")
                    else:
                        error_msg = data.get('message', 'Unknown error')
                        print(f"   ❌ 服务器返回错误状态: {error_msg}")
                else:
                    print("   ❌ 响应中没有 status 字段")
                    
            except json.JSONDecodeError:
                print(f"   ❌ 响应不是有效的 JSON")
                print(f"   响应内容: {response.text[:200]}...")
                
        else:
            print(f"   ❌ HTTP 错误: {response.status_code}")
            print(f"   错误响应: {response.text[:200]}...")
            
    except requests.exceptions.ConnectionError:
        print("   ❌ 无法连接到服务器 - 请检查服务器地址")
    except requests.exceptions.Timeout:
        print("   ❌ 连接超时 - 请检查网络或服务器状态")
    except Exception as e:
        print(f"   ❌ 请求异常: {e}")
    
    print("\n" + "=" * 50)
    print("💡 常见问题排查:")
    print("1. 检查 CookieCloud 服务器是否正常运行")
    print("2. 确认 UUID 和密码是否正确")
    print("3. 确认浏览器插件已成功同步 Cookie")
    print("4. 检查服务器地址是否可从外网访问")

if __name__ == "__main__":
    debug_cookiecloud()