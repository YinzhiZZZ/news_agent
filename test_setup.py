# test_setup.py
# 运行这个脚本验证：环境正常 + 第一个 RSS 源可以采集
# 命令：python test_setup.py

import sys
import feedparser
from sources import get_priority_sources
from config import USER_PROFILE, SUMMARY_FORMAT

def check_imports():
    print("✓ feedparser 安装正常")
    try:
        import anthropic
        print("✓ anthropic SDK 安装正常")
    except ImportError:
        print("✗ anthropic 未安装，请运行：pip install anthropic")
    try:
        import requests
        print("✓ requests 安装正常")
    except ImportError:
        print("✗ requests 未安装")
    try:
        from dotenv import load_dotenv
        print("✓ python-dotenv 安装正常")
    except ImportError:
        print("✗ python-dotenv 未安装")

def check_config():
    print(f"\n用户：{USER_PROFILE['name']}")
    print(f"关注领域：{', '.join(USER_PROFILE['domains'].keys())}")
    print(f"摘要字段数：{len(SUMMARY_FORMAT)} 个")
    print("✓ config.py 加载正常")

def test_one_rss():
    sources = get_priority_sources(max_priority=1)
    # 用第一个源测试
    test_source = sources[0]
    print(f"\n测试采集：{test_source['name']}")
    print(f"URL: {test_source['url']}")

    feed = feedparser.parse(test_source["url"])

    if feed.bozo:
        print(f"✗ 解析失败：{feed.bozo_exception}")
        return

    entries = feed.entries
    print(f"✓ 成功采集 {len(entries)} 篇文章")

    if entries:
        first = entries[0]
        print(f"\n最新一篇：")
        print(f"  标题：{first.get('title', '无标题')}")
        print(f"  链接：{first.get('link', '无链接')}")
        print(f"  时间：{first.get('published', '无时间')}")

def list_all_sources():
    sources = get_priority_sources(max_priority=1)
    print(f"\n当前配置了 {len(sources)} 个 Priority-1 订阅源：")
    current_domain = None
    for s in sources:
        if s["domain"] != current_domain:
            current_domain = s["domain"]
            domain_name = USER_PROFILE["domains"][current_domain]["name"]
            print(f"\n  [{domain_name}]")
        print(f"    - {s['name']} ({s['lang'].upper()})")

if __name__ == "__main__":
    print("=" * 50)
    print("资讯 Agent — 环境验证")
    print("=" * 50)

    print("\n[1] 检查依赖包")
    check_imports()

    print("\n[2] 检查配置文件")
    check_config()

    print("\n[3] 测试第一个 RSS 源")
    test_one_rss()

    print("\n[4] 全部订阅源列表")
    list_all_sources()

    print("\n" + "=" * 50)
    print("如果以上全部显示 ✓，你可以进入下一步了！")
