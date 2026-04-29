# collector/fetch_rss.py
# 采集 Agent 的第一个 Skill：从 RSS 订阅源批量抓取文章
#
# 这个文件做三件事：
#   1. 遍历 sources.py 里的订阅源列表
#   2. 用 feedparser 解析每个 RSS feed
#   3. 把结果整理成统一的字典格式，交给处理 Agent

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import feedparser
import time
from datetime import datetime, timezone
from sources import get_priority_sources, TIER_1_RSS


# ── 核心函数：采集单个 RSS 源 ──────────────────────────────────────────────────

def fetch_single_source(source: dict, max_items: int = 30) -> list[dict]:
    """
    采集一个 RSS 订阅源，返回文章列表。

    参数：
        source    : sources.py 里的单个源配置字典
        max_items : 每个源最多采集多少篇（避免某些源文章量过大）

    返回：
        文章列表，每篇文章是一个字典，包含统一格式的字段
    """
    print(f"  正在采集：{source['name']}...")

    # feedparser.parse() 是核心调用
    # 它会自动处理 RSS 和 Atom 两种格式，你不需要区分
    feed = feedparser.parse(source["url"])

    # bozo 是 feedparser 的错误标志
    # True 表示 XML 解析出了问题（但有时有错也能拿到数据）
    if feed.bozo and not feed.entries:
        print(f"    ✗ 采集失败：{source['name']} — {feed.bozo_exception}")
        return []

    articles = []

    for entry in feed.entries[:max_items]:

        # 发布时间处理：feedparser 会把时间解析成一个 struct_time 元组
        # 我们把它转成可读的字符串格式
        published = ""
        if hasattr(entry, "published_parsed") and entry.published_parsed:
            try:
                dt = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
                published = dt.strftime("%Y-%m-%d %H:%M")
            except Exception:
                published = entry.get("published", "")
        else:
            published = entry.get("published", "")

        # 正文摘要：RSS 里的 summary 通常是文章开头几句话
        # 有些源用 content 字段存完整正文
        summary_text = ""
        if hasattr(entry, "content") and entry.content:
            summary_text = entry.content[0].get("value", "")[:2000]
        elif hasattr(entry, "summary"):
            summary_text = entry.summary[:2000]

        # 作者字段
        author = entry.get("author", "")

        # 整理成统一格式
        # 这个格式就是后续处理 Agent 的输入格式
        article = {
            "title":       entry.get("title", "无标题"),
            "url":         entry.get("link", ""),
            "author":      author,
            "published_at": published,
            "raw_summary": summary_text,   # RSS 自带的原始摘要，还没经过 AI 处理
            "source_name": source["name"],
            "source_url":  source["url"],
            "domain":      source["domain"],
            "lang":        source["lang"],
            "priority":    source["priority"],
        }
        articles.append(article)

    print(f"    ✓ {source['name']}：采集到 {len(articles)} 篇")
    return articles


# ── 批量采集：遍历所有订阅源 ──────────────────────────────────────────────────

def fetch_all_sources(
    max_priority: int = 1,
    max_items_per_source: int = 20,
    delay_seconds: float = 0.5,
) -> list[dict]:
    """
    批量采集所有订阅源，返回合并后的文章列表。

    参数：
        max_priority          : 只采集优先级 <= 此值的源（1=只采高优先级）
        max_items_per_source  : 每个源最多取多少篇
        delay_seconds         : 每个源之间的间隔秒数（避免请求太频繁被封）

    返回：
        所有源合并后的文章列表，按 domain 分组
    """
    sources = get_priority_sources(max_priority=max_priority)
    all_articles = []

    print(f"\n开始采集，共 {len(sources)} 个订阅源\n")
    print("=" * 50)

    for i, source in enumerate(sources, 1):
        print(f"[{i}/{len(sources)}] {source['domain'].upper()}")
        articles = fetch_single_source(source, max_items=max_items_per_source)
        all_articles.extend(articles)

        # 每个源之间稍微等一下
        # 原因：如果你连续快速请求同一个服务器，可能会被认为是爬虫攻击而封 IP
        if i < len(sources):
            time.sleep(delay_seconds)

    print("=" * 50)
    print(f"\n采集完成：共 {len(all_articles)} 篇文章")
    print_summary(all_articles)

    return all_articles


# ── 辅助函数：打印采集结果摘要 ────────────────────────────────────────────────

def print_summary(articles: list[dict]):
    """按领域统计采集结果"""
    from collections import Counter
    domain_counts = Counter(a["domain"] for a in articles)

    print("\n按领域分布：")
    domain_names = {
        "ai": "AI 与技术",
        "photography": "摄影",
        "travel": "旅游与地理",
        "business": "商业与互联网",
    }
    for domain, count in sorted(domain_counts.items()):
        name = domain_names.get(domain, domain)
        print(f"  {name}: {count} 篇")


# ── 直接运行这个文件时执行测试 ────────────────────────────────────────────────
# python collector/fetch_rss.py

if __name__ == "__main__":
    # 先只测试优先级最高的源
    articles = fetch_all_sources(
        max_priority=1,
        max_items_per_source=5,  # 测试时每个源只取 5 篇，跑得快
    )

    print("\n── 第一篇文章的完整字段 ──")
    if articles:
        first = articles[0]
        for key, value in first.items():
            # raw_summary 太长，只显示前 100 字
            if key == "raw_summary":
                print(f"  {key}: {str(value)[:100]}...")
            else:
                print(f"  {key}: {value}")
