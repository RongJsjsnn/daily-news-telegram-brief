# 每日自动新闻推送程序

这是一个 Python MVP 版本的“每日战略新闻简报”推送程序。它会在 Asia/Shanghai 时区的每个工作日 08:00 抓取最近 24 小时 RSS 新闻，去重、分类、排序后生成中文 Markdown 简报，并通过配置的通知渠道发送。

默认 RSS 已优先选择当前可公开访问的来源，包括 BBC 中文、央视 RSS、36 氪、财新，以及用于补齐板块覆盖的 Google News RSS 查询源。AP、Reuters、新华社、LatePost、中国饭店协会等来源如果使用授权 API、付费 RSS 或网站结构变化后的新地址，可以通过 `.env` 的 `RSS_FEEDS_JSON` 直接接入。

## 功能

- 默认工作日 08:00 自动执行，时区为 `Asia/Shanghai`
- 支持 RSS 新闻源，优先使用稳定 RSS/API，后续可扩展网页抓取
- 抓取最近 24 小时新闻
- 自动去重、过滤军事相关内容、按重要性排序
- 输出统一为简体中文的 Markdown 格式“全球战略内参”风格简报
- 板块包括国际政治、国内新闻、经济、科技、文化、餐饮
- 每条新闻包含普通人影响、中国经济影响、未来半年预测、大国博弈逻辑、餐饮业尤其万州餐饮影响、一句话核心判断
- SMTP 邮件同时包含 HTML 正文和纯文本备用版本，兼容 Outlook、Gmail 和 Apple Mail
- 支持企业微信机器人、Telegram、SMTP 邮件、本地文件输出
- 支持失败重试、日志记录和异常报警
- API Key 和 Webhook 均通过 `.env` 管理，不写死在代码里

## 安装

```bash
cd news-push
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

编辑 `.env`，选择推送渠道。

## 推送渠道配置

### 本地文件

最容易验证的方式：

```env
NOTIFIER=file
OUTPUT_DIR=./output
```

运行后会在 `output/` 生成 Markdown 简报。

### 企业微信机器人

```env
NOTIFIER=wecom
WECOM_WEBHOOK_URL=https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=你的key
```

企业微信机器人 Markdown 单条消息长度有限，程序会自动截断到约 3900 字。若希望完整长文推送，建议改用邮件或将企业微信模块扩展为分段发送。

### Telegram

```env
NOTIFIER=telegram
TELEGRAM_BOT_TOKEN=你的bot_token
TELEGRAM_CHAT_ID=你的chat_id
```

Telegram 会按长度自动分段发送。

### SMTP 邮件

```env
NOTIFIER=smtp
SMTP_HOST=smtp.example.com
SMTP_PORT=465
SMTP_USER=你的邮箱账号
SMTP_PASSWORD=你的邮箱授权码
SMTP_FROM=你的邮箱账号
SMTP_TO=接收邮箱
SMTP_USE_SSL=true
```

## 运行

立即运行一次：

```bash
python main.py once
```

启动定时任务：

```bash
python main.py schedule
```

不带参数时默认启动定时任务：

```bash
python main.py
```

日志默认写入：

```text
logs/news_push.log
```

## 清理旧简报

项目包含一个旧简报清理脚本：

```bash
python cleanup.py
```

默认只删除 `output/` 中超过 15 天的 `*_brief.md`，以及 `logs/` 中超过 60 天的日志。可在 `.env` 中调整：

```env
CLEANUP_BRIEF_RETENTION_DAYS=15
CLEANUP_LOG_RETENTION_DAYS=60
```

## 部署方式

### 推荐：GitHub Actions 云端运行

如果电脑会休眠、关机或断网，本机定时任务无法保证执行。最稳妥的方式是放到 GitHub Actions、云服务器、NAS 等不会睡眠的环境运行。

本项目已提供 GitHub Actions 模板：

```text
.github/workflows/daily-news-telegram.yml
```

它会在每个工作日北京时间 08:00 自动执行，并通过 Telegram 发送简报。使用步骤：

1. 把项目推送到 GitHub 仓库。
2. 在仓库 `Settings -> Secrets and variables -> Actions -> New repository secret` 中添加：
   - `BOT_TOKEN`
   - `CHAT_ID`
3. 确认仓库已启用 Actions。
4. 进入 `Actions -> Daily News Telegram Brief`，可以手动点 `Run workflow` 测试一次。

注意：不要把本地 `news-push/.env` 提交到 GitHub，里面有 Telegram Token。项目根目录已添加 `.gitignore`，默认会忽略 `.env`、虚拟环境、简报输出和日志。

### 方式一：长期运行进程

适合个人服务器、云主机、NAS：

```bash
cd /path/to/news-push
source .venv/bin/activate
python main.py schedule
```

建议配合 `systemd`、`supervisor` 或 Docker 保活。

### 方式二：系统 Cron

如果不希望程序常驻，可以让系统每天工作日 08:00 拉起一次：

```cron
0 8 * * 1-5 cd /path/to/news-push && /path/to/news-push/.venv/bin/python main.py once
```

Cron 方式下，程序内部调度器不需要启动。

## 自定义新闻源

可以在 `.env` 中用 `RSS_FEEDS_JSON` 覆盖默认源：

```env
RSS_FEEDS_JSON=[{"name":"BBC中文","url":"https://feeds.bbci.co.uk/zhongwen/simp/rss.xml","category_hint":"international","reliability":0.88},{"name":"36氪","url":"https://36kr.com/feed","category_hint":"technology","reliability":0.72}]
```

字段说明：

- `name`：来源名称
- `url`：RSS 地址
- `category_hint`：默认分类，可选 `international`、`domestic`、`economy`、`technology`、`culture`、`restaurant`
- `reliability`：来源可靠度，0 到 1 之间

默认 RSS 地址可能随媒体网站调整而变化。如果某个来源长期抓取失败，直接在 `.env` 替换为新的 RSS/API 地址即可。

## 后续优化建议

- 接入付费新闻 API，提高来源稳定性和覆盖率
- 增加 LLM 摘要模块，使每条新闻分析更贴近原文事实
- 对企业微信支持长文分段推送
- 增加网页抓取 fallback
- 增加数据库记录，避免跨天重复推送同一事件
