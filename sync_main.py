import requests
import json
import time

# 基础headers
BASE_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
}

# API headers模板
def get_api_headers(cookie_str, book_id):
    return {
        'Cookie': cookie_str,
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': f'https://weread.qq.com/web/reader/{book_id}',
        'Origin': 'https://weread.qq.com',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'sec-ch-ua': '"Google Chrome";v="135", "Not-A.Brand";v="8", "Chromium";v="135"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-origin',
    }

def refresh_session_simple(session, current_cookie):
    """刷新cookie会话"""
    print("🔄 正在刷新微信读书会话...")
    
    try:
        # 访问主页
        print("🔍 访问: https://weread.qq.com/")
        home_resp = session.get("https://weread.qq.com/", headers=BASE_HEADERS, timeout=10)
        
        # 访问书架
        print("🔍 访问: https://weread.qq.com/web/shelf")
        shelf_resp = session.get("https://weread.qq.com/web/shelf", headers=BASE_HEADERS, timeout=10)
        
        # 获取新cookie
        new_cookie = '; '.join([f"{c.name}={c.value}" for c in session.cookies])
        
        # 验证必要cookie
        cookies_dict = session.cookies.get_dict()
        required_cookies = ['wr_skey', 'wr_rtken']
        missing = [c for c in required_cookies if c not in cookies_dict]
        
        if missing:
            print(f"❌ 缺少必要cookie: {missing}")
            return False, session, current_cookie
            
        print("✅ Cookie刷新成功")
        return True, session, new_cookie
        
    except Exception as e:
        print(f"❌ 刷新会话异常: {e}")
        return False, session, current_cookie

def get_bookmark_list(session, book_id, wx_cookie):
    """获取划线列表"""
    print(f"📝 获取划线: {book_id}")
    
    # 统一处理cookie格式
    if isinstance(wx_cookie, tuple):
        cookie_str = wx_cookie[2] if len(wx_cookie) > 2 else str(wx_cookie)
    elif isinstance(wx_cookie, dict):
        cookie_str = '; '.join([f"{k}={v}" for k, v in wx_cookie.items()])
    else:
        cookie_str = wx_cookie
    
    try:
        url = "https://weread.qq.com/web/book/bookmarklist"
        params = {"bookId": book_id}
        headers = get_api_headers(cookie_str, book_id)
        
        response = session.get(url, params=params, headers=headers, timeout=30)
        data = response.json()
        
        if data.get('errCode') == -2012:
            print("❌ 登录超时，尝试刷新cookie...")
            success, updated_session, new_cookie = refresh_session_simple(session, wx_cookie)
            if success:
                return get_bookmark_list(updated_session, book_id, new_cookie)
            else:
                raise Exception("Cookie刷新失败")
        
        print(f"✅ 获取划线成功: {len(data.get('updated', []))} 条")
        return data
        
    except Exception as e:
        print(f"❌ 获取划线失败: {e}")
        raise

def get_review_list(session, book_id, wx_cookie):
    """获取笔记和评论"""
    print(f"📖 获取笔记: {book_id}")
    
    # 统一处理cookie格式
    if isinstance(wx_cookie, tuple):
        cookie_str = wx_cookie[2] if len(wx_cookie) > 2 else str(wx_cookie)
    elif isinstance(wx_cookie, dict):
        cookie_str = '; '.join([f"{k}={v}" for k, v in wx_cookie.items()])
    else:
        cookie_str = wx_cookie
    
    try:
        url = "https://weread.qq.com/web/book/notebook"
        params = {"bookId": book_id}
        headers = get_api_headers(cookie_str, book_id)
        
        response = session.get(url, params=params, headers=headers, timeout=30)
        data = response.json()
        
        if data.get('errCode') == -2012:
            print("❌ 登录超时，尝试刷新cookie...")
            success, updated_session, new_cookie = refresh_session_simple(session, wx_cookie)
            if success:
                return get_review_list(updated_session, book_id, new_cookie)
            else:
                raise Exception("Cookie刷新失败")
        
        print("✅ 获取笔记成功")
        return data
        
    except Exception as e:
        print(f"❌ 获取笔记失败: {e}")
        raise