# wxreaderToNotion
tongbu 
# 微信读书到 Notion 同步工具

使用 GitHub Actions 自动同步微信读书的划线、笔记到 Notion。

## 🚀 功能特点

- 自动同步微信读书划线笔记到 Notion
- 支持定时同步（每天凌晨2点）
- 支持手动触发同步
- 完整的错误处理和日志

## ⚙️ 设置步骤

### 1. 配置 GitHub Secrets

在仓库 Settings → Secrets and variables → Actions 中添加：

- `WEREAD_REFRESH_TOKEN`: 微信读书的刷新令牌
- `NOTION_TOKEN`: Notion 集成令牌
- `NOTION_DATABASE_ID`: Notion 数据库 ID

### 2. 创建 Notion 数据库

在 Notion 中创建数据库，包含以下属性：
- 书名 (Title)
- 作者 (Text) 
- 章节 (Text)
- 日期 (Date)

### 3. 配置微信读书 API

注意：当前为示例版本，需要后续配置真实的微信读书 API 调用。

## 🎯 使用方法

- **自动运行**: 每天 UTC 时间 18:00（北京时间凌晨2点）
- **手动运行**: 在 GitHub Actions 页面手动触发工作流

## 📁 项目结构
