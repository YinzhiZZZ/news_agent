# CLAUDE.md — news_agent 项目规范

个人资讯 Agent：自动采集 RSS → 抓取全文 → AI 摘要 → 评分排序 → 推送邮件。

## 环境启动

```bash
# 激活虚拟环境（Windows）
news_env\Scripts\activate

# 验证环境
python test_setup.py
```

运行时加 `PYTHONIOENCODING=utf-8` 避免 Windows 控制台中文乱码：

```bash
PYTHONIOENCODING=utf-8 news_env/Scripts/python.exe pipeline.py
```

## 项目结构（四层架构）

```
news_agent/
├── config.py              # 用户画像、评分权重、DIGEST_CONFIG（领域配额、发送时间）
├── sources.py             # RSS 订阅源列表（Tier 1 直连 / Tier 2 需 RSSHub）
├── pipeline.py            # 完整流程入口，串联下面四层
│
├── collector/
│   ├── fetch_rss.py       # 采集层：解析 RSS → list[article dict]
│   └── scrape_web.py      # 采集层：抓取网页全文 → 补充 full_content 字段
│                          #   优化：raw_summary > 200 字直接复用，跳过网络请求
│
├── processor/
│   ├── summarize.py       # 处理层：调用 Claude API → 10 字段结构化摘要
│   └── score_relevance.py # 处理层：三维评分（相关性/质量/新颖性）+ Jaccard 去重
│
├── publisher/
│   └── send_digest.py     # 推送层：按领域配额筛选 → 生成 HTML 网页 + 发送邮件
│
└── output/
    ├── digest.json              # 当日摘要（pipeline.py 输出）
    └── digest_YYYY-MM-DD.html   # 网页版（send_digest.py 输出）
```

## 运行完整 Pipeline

```bash
# 一键运行（采集 → 全文 → 摘要 → 保存 digest.json）
PYTHONIOENCODING=utf-8 news_env/Scripts/python.exe pipeline.py

# 评分排序（读取 digest.json，打分后打印排名）
PYTHONIOENCODING=utf-8 news_env/Scripts/python.exe processor/score_relevance.py

# 推送（生成 HTML + 发邮件）
PYTHONIOENCODING=utf-8 news_env/Scripts/python.exe publisher/send_digest.py
```

单模块独立测试：

```bash
python collector/fetch_rss.py       # 采集 RSS，打印各领域文章数
python collector/scrape_web.py      # 测试单 URL 抓取
python processor/summarize.py       # 用内置样本文章测试摘要
```

## .env 必填字段

```
ANTHROPIC_API_KEY=        # Anthropic API 密钥

GMAIL_SENDER=             # 发件人 Gmail 地址
GMAIL_RECIPIENT=          # 收件人邮箱
GMAIL_APP_PASSWORD=       # Gmail 应用专用密码（16位，需开启两步验证）
                          # 获取：myaccount.google.com/apppasswords

GITHUB_PAGES_URL=         # 可选：部署后的网页根 URL，供邮件底部"查看网页版"链接使用
                          # 示例：https://yourname.github.io/news-digest
```

## 核心设计决策

| 项目 | 当前值 | 说明 |
|------|--------|------|
| 摘要模型 | `claude-haiku-4-5-20251001` | 速度/成本优化 |
| 评分模型 | `claude-haiku-4-5-20251001` | 同上 |
| 网页全文上限 | 4000 字符 | 送入 Claude 时截至 3500 |
| 全文跳过阈值 | raw_summary > 200 字 | 直接复用，不发网络请求 |
| 每日收录上限 | 8 篇 | `DIGEST_CONFIG["max_articles"]` |
| 领域配额 | AI 3 / 商业 3 / 摄影 1 / 旅游 1 | `DIGEST_CONFIG["domain_quota"]` |
| 最低入选分 | 5.0 | `MIN_SCORE_THRESHOLD` |
| 评分权重 | 相关性 50% / 质量 30% / 新颖性 20% | `SCORING_WEIGHTS` |
| 请求间隔 | RSS 0.5s / 抓取 1.0s / Claude 0.3s | 避免被封 |

## Tier 2 信源说明

`sources.py` 里的 `TIER_2_RSSHUB`（微信公众号、知乎、B站、微博）需要本地部署 RSSHub 实例才能使用，默认不启用。
