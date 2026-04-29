# collector/scrape_web.py
# 采集 Agent 的第二个 Skill：抓取网页全文
#
# 输入：一篇文章的 URL
# 输出：该网页的正文内容（去掉导航栏、广告、脚注等噪音）
#
# 在整个流程中的位置：
#   fetch_rss 拿到标题和链接 → scrape_web 打开链接抓全文 → summarize 基于全文做摘要

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
from bs4 import BeautifulSoup
import time


# ── 核心函数：抓取单个网页的正文 ──────────────────────────────────────────────

def scrape_web(url: str, timeout: int = 10) -> dict:
    """
    打开一个网页 URL，提取正文内容。

    参数：
        url     : 要抓取的网页地址
        timeout : 超时秒数，超过这个时间就放弃，避免一个慢网页卡住整个流程

    返回：
        包含正文内容的字典，失败时返回 None
    """

    # 设置请求头，模拟真实浏览器访问
    # 不加这个，很多网站会拒绝请求（因为它们会屏蔽明显的爬虫请求）
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    }

    try:
        response = requests.get(url, headers=headers, timeout=timeout)

        # 检查 HTTP 状态码
        # 200 = 成功，4xx = 客户端错误（比如 403 拒绝访问），5xx = 服务器错误
        if response.status_code != 200:
            print(f"    ⚠ 抓取失败 ({response.status_code})：{url[:60]}")
            return None

        # 用 BeautifulSoup 解析 HTML
        # "html.parser" 是 Python 内置的解析器，不需要额外安装
        soup = BeautifulSoup(response.text, "html.parser")

        # 去掉噪音标签：脚本、样式、导航、页脚、广告、侧边栏
        # 这些标签里的文字不是文章内容，留着会干扰摘要质量
        noise_tags = ["script", "style", "nav", "footer", "aside",
                      "header", "advertisement", "figure"]
        for tag in soup(noise_tags):
            tag.decompose()  # decompose() 是完全删除这个标签和它的内容

        # 提取标题
        title = ""
        if soup.find("h1"):
            title = soup.find("h1").get_text(strip=True)

        # 提取正文
        # 策略：优先找 <article> 标签（大多数现代网站把正文放在这里）
        # 找不到就退而求其次，找所有 <p> 段落
        content = ""
        article_tag = soup.find("article")

        if article_tag:
            # 找到 <article>，提取里面所有段落
            paragraphs = article_tag.find_all("p")
        else:
            # 没有 <article>，从整个页面找段落
            paragraphs = soup.find_all("p")

        # 把所有段落拼接起来
        # 过滤掉太短的段落（少于 30 个字符），那些通常是按钮文字或标签
        content = "\n".join(
            p.get_text(strip=True)
            for p in paragraphs
            if len(p.get_text(strip=True)) > 30
        )

        # 控制长度：最多保留 4000 字符
        # 原因：Claude API 按 token 计费，正文太长会增加成本
        # 4000 字符大约是一篇中等长度文章，对于摘要任务已经足够
        content = content[:4000]

        if not content:
            print(f"    ⚠ 正文为空（可能是付费墙或动态加载）：{url[:60]}")
            return None

        return {
            "title":   title,
            "content": content,
            "url":     url,
            "chars":   len(content),
        }

    except requests.exceptions.Timeout:
        print(f"    ⚠ 超时：{url[:60]}")
        return None
    except requests.exceptions.ConnectionError:
        print(f"    ⚠ 连接失败：{url[:60]}")
        return None
    except Exception as e:
        print(f"    ⚠ 未知错误：{e}")
        return None


# ── 批量抓取：为文章列表补充全文 ─────────────────────────────────────────────

def enrich_with_fulltext(articles: list[dict], delay_seconds: float = 1.0) -> list[dict]:
    """
    为文章列表里的每篇文章抓取全文，补充到 full_content 字段。

    参数：
        articles       : fetch_rss.py 返回的原始文章列表
        delay_seconds  : 每次请求之间的间隔秒数
                         比 RSS 采集间隔更长，因为是直接请求对方网站，要更礼貌

    返回：
        每篇文章新增了 full_content 字段：
          - 成功：full_content = 正文字符串
          - 失败：full_content = "" （后续 summarize 会用 raw_summary 兜底）
    """
    print(f"\n开始抓取全文，共 {len(articles)} 篇")
    print("=" * 50)

    success_count = 0

    for i, article in enumerate(articles, 1):
        print(f"[{i}/{len(articles)}] {article['title'][:50]}...")

        raw_summary = article.get("raw_summary", "")
        if len(raw_summary) > 200:
            article["full_content"] = raw_summary
            success_count += 1
            print(f"    ✓ 使用 raw_summary（{len(raw_summary)} 字符），跳过抓取")
            continue

        result = scrape_web(article["url"])

        if result and result["content"]:
            article["full_content"] = result["content"]
            success_count += 1
            print(f"    ✓ 抓取成功：{result['chars']} 字符")
        else:
            # 抓取失败不报错，用空字符串占位
            # summarize.py 会检测这个字段，失败时用 raw_summary 兜底
            article["full_content"] = ""

        if i < len(articles):
            time.sleep(delay_seconds)

    print("=" * 50)
    print(f"全文抓取完成：{success_count}/{len(articles)} 篇成功\n")

    return articles


# ── 直接运行这个文件时执行测试 ────────────────────────────────────────────────
# python collector\scrape_web.py

if __name__ == "__main__":
    test_url = "https://openai.com/index/openai-on-aws"
    print(f"测试抓取：{test_url}\n")

    result = scrape_web(test_url)

    if result:
        print(f"标题：{result['title']}")
        print(f"正文字符数：{result['chars']}")
        print(f"\n正文前 500 字：\n{result['content'][:500]}...")
    else:
        print("抓取失败，这个 URL 可能有访问限制")
        print("这是正常情况，部分网站会拒绝非浏览器访问")
