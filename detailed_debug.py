import os
import requests
import json

def detailed_debug():
    server_url = os.getenv('COOKIECLOUD_SERVER')
    uuid = os.getenv('COOKIECLOUD_UUID')
    
    print("🔍 详细诊断 CookieCloud")
    print("=" * 60)
    
    if not server_url or not uuid:
        print("❌ 缺少必要的环境变量")
        return
    
    # 测试基础连接
    test_urls = [
        server_url.rstrip('/'),  # 基础URL
        f"{server_url.rstrip('/')}/get/{uuid}",  # 完整API URL
    ]
    
    for test_url in test_urls:
        print(f"\n🔗 测试 URL: {test_url}")
        print("-" * 40)
        
        try:
            response = requests.get(test_url, timeout=10, allow_redirects=True)
            
            print(f"📡 状态码: {response.status_code}")
            print(f"📍 最终URL: {response.url}")
            print(f"📏 内容长度: {len(response.text)} 字符")
            print(f"🎯 内容类型: {response.headers.get('content-type', '未知')}")
            
            # 检查是否是重定向
            if len(response.history) > 0:
                print(f"🔄 发生了重定向:")
                for i, resp in enumerate(response.history):
                    print(f"   {i+1}. {resp.status_code} -> {resp.url}")
            
            # 分析响应内容
            content = response.text.strip()
            
            if response.status_code == 200:
                # 尝试解析为 JSON
                try:
                    data = json.loads(content)
                    print("✅ 响应是有效的 JSON")
                    print(f"📊 JSON 键: {list(data.keys())}")
                    if 'status' in data:
                        print(f"🎯 找到 status 字段: {data['status']}")
                    else:
                        print("❌ 没有 status 字段")
                    print(f"📄 JSON 内容: {json.dumps(data, ensure_ascii=False, indent=2)}")
                    
                except json.JSONDecodeError:
                    print("❌ 响应不是有效的 JSON")
                    # 检查是否是 HTML 页面
                    if content.startswith('<!DOCTYPE') or content.startswith('<html') or '<html' in content.lower():
                        print("📄 响应是 HTML 页面")
                        # 提取 title
                        import re
                        title_match = re.search(r'<title>(.*?)</title>', content, re.IGNORECASE)
                        if title_match:
                            print(f"📝 页面标题: {title_match.group(1)}")
                        # 显示前500个字符
                        print(f"📖 内容预览: {content[:500]}...")
                    else:
                        print(f"📖 原始内容: {content[:1000]}...")
                        
            elif response.status_code in [404, 500, 502, 503]:
                print(f"❌ 服务器错误: {response.status_code}")
                print(f"📖 错误页面: {content[:500]}...")
                
            else:
                print(f"⚠️ 非200状态码: {response.status_code}")
                print(f"📖 响应内容: {content[:500]}...")
                
        except requests.exceptions.ConnectionError:
            print("❌ 无法连接到服务器 - 请检查服务器地址和网络")
        except requests.exceptions.Timeout:
            print("❌ 连接超时 - 服务器可能无法访问")
        except Exception as e:
            print(f"💥 请求异常: {e}")

if __name__ == "__main__":
    detailed_debug()