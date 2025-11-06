import os
import time
from datetime import datetime
from weread_api import WeReadAPI
from notion_client import NotionClient

def main():
    print("🚀 微信读书到Notion同步开始")
    print("=" * 50)
    
    # 初始化客户端
    weread = WeReadAPI(
        os.getenv('COOKIECLOUD_SERVER'),
        os.getenv('COOKIECLOUD_UUID'), 
        os.getenv('COOKIECLOUD_PASSWORD')
    )
    
    notion = NotionClient()
    
    # 测试连接
    if not weread.test_connection():
        print("❌ 微信读书连接失败")
        return
    
    print("✅ 微信读书连接成功")
    
    # 获取书架
    books = weread.get_bookshelf()
    if not books:
        print("❌ 未获取到书籍")
        return
    
    # 处理前3本书
    success_count = 0
    for i, book in enumerate(books[:3]):
        book_id = book['bookId']
        book_title = book['title']
        book_author = book.get('author', '未知')
        
        print(f"\n📖 处理第{i+1}本书: {book_title}")
        
        # 获取划线
        highlights = weread.get_book_highlights(book_id)
        
        for highlight in highlights:
            if highlight.get('markText'):
                highlight_data = {
                    'book_title': book_title,
                    'author': book_author,
                    'chapter': highlight.get('chapterTitle', '未知章节'),
                    'highlight': highlight.get('markText', ''),
                    'note': highlight.get('content', ''),
                    'date': datetime.now().isoformat() + 'Z'
                }
                
                # 同步到Notion
                if notion.create_highlight_page(highlight_data):
                    success_count += 1
        
        time.sleep(1)  # 避免请求过快
    
    print(f"\n🎉 同步完成! 成功同步{success_count}条划线到Notion")

if __name__ == "__main__":
    main()