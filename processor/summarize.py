# processor/summarize.py
# 处理 Agent 的第一个 Skill：调用 Claude API 生成结构化摘要
#
# 更新：接入 scrape_web 全文抓取 + 优化 Prompt 约束
#
# 数据流：
#   fetch_rss（标题+链接）→ scrape_web（全文）→ summarize（结构化摘要）

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import time
from dotenv import load_dotenv
import anthropic
from config import USER_PROFILE
from collector.scrape_web import enrich_with_fulltext

load_dotenv()
client = anthropic.Anthropic(timeout=30.0)


def summarize_article(article: dict) -> dict:
    content_to_use = article.get("full_content") or article.get("raw_summary", "")
    content_source = "全文" if article.get("full_content") else "RSS摘要片段（未能获取全文）"

    domain_info = USER_PROFILE["domains"].get(article["domain"], {})
    domain_name = domain_info.get("name", article["domain"])
    domain_preference = domain_info.get("preferred_content", "")

    prompt = f"""你是一个资讯整理助手。请根据以下文章内容生成结构化摘要。

文章信息：
- 标题：{article['title']}
- 来源：{article['source_name']}
- 原文链接：{article['url']}
- 作者：{article['author'] if article['author'] else '未署名'}
- 发布时间：{article['published_at']}
- 所属领域：{domain_name}
- 内容来源：{content_source}

文章内容：
{content_to_use[:3500]}

读者偏好：{domain_preference}

请严格按照以下 JSON 格式返回，不要输出任何其他文字：

{{
  "source_name": "媒体/网站名称",
  "source_url": "原文链接",
  "author": "作者姓名，无法确定填'未署名'",
  "author_bio": "作者简介：职位和擅长领域（从文章内容或署名推断，无法确定填'暂无信息'）",
  "published_at": "发布时间，格式 YYYY-MM-DD HH:MM",
  "domain": "所属领域中文名",
  "main_topic": "核心话题，一个简短短语",
  "related_topics": ["相关话题标签1", "相关话题标签2", "相关话题标签3"],
  "references": ["文中引用的具体报告、数据来源或外部链接，没有则返回空数组"],
  "summary": "3-5句话，必须包含：①核心事件及背景是什么 ②涉及的具体数字、产品名或公司名 ③对{domain_name}领域的实际影响。禁止使用'该文章介绍了'等套话，直接陈述事实。"
}}"""

    max_retries = 3
    for attempt in range(1, max_retries + 1):
        try:
            response = client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=800,
                messages=[{"role": "user", "content": prompt}]
            )
            break
        except Exception as e:
            if attempt < max_retries:
                print(f"    [!] API 连接失败（第 {attempt} 次），5 秒后重试：{e}")
                time.sleep(5)
            else:
                print(f"    ✗ API 调用失败，已重试 {max_retries} 次：{e}")
                return None

    try:
        raw_text = response.content[0].text.strip()
        if raw_text.startswith("```"):
            raw_text = raw_text.split("```")[1]
            if raw_text.startswith("json"):
                raw_text = raw_text[4:]

        result = json.loads(raw_text.strip())

        defaults = {
            "source_name":    article["source_name"],
            "source_url":     article["url"],
            "author":         article["author"] or "未署名",
            "author_bio":     "暂无信息",
            "published_at":   article["published_at"],
            "domain":         domain_name,
            "main_topic":     article["title"],
            "related_topics": [],
            "references":     [],
            "summary":        content_to_use[:200],
        }
        for field, default in defaults.items():
            if field not in result:
                result[field] = default

        return result

    except json.JSONDecodeError:
        print(f"    ⚠ JSON 解析失败，使用原始内容兜底")
        return {
            "source_name":    article["source_name"],
            "source_url":     article["url"],
            "author":         article["author"] or "未署名",
            "author_bio":     "暂无信息",
            "published_at":   article["published_at"],
            "domain":         domain_name,
            "main_topic":     article["title"],
            "related_topics": [],
            "references":     [],
            "summary":        content_to_use[:300],
        }



def summarize_all(articles: list[dict], delay_seconds: float = 0.3) -> list[dict]:
    print(f"\n开始生成摘要，共 {len(articles)} 篇")
    print(f"预计耗时约 {round(len(articles) * 1.5)} 秒\n")
    print("=" * 50)

    results = []
    for i, article in enumerate(articles, 1):
        print(f"[{i}/{len(articles)}] {article['source_name']} — {article['title'][:45]}...")
        result = summarize_article(article)
        if result:
            results.append(result)
            print(f"    ✓ {result['main_topic']}")
        if i < len(articles):
            time.sleep(delay_seconds)

    print("=" * 50)
    print(f"\n摘要完成：{len(results)}/{len(articles)} 篇成功")
    return results


if __name__ == "__main__":
    print("=" * 50)
    print("完整流程测试：采集 → 全文抓取 → 摘要")
    print("=" * 50)

    test_articles = [
        {
            "title": "OpenAI models, Codex, and Managed Agents come to AWS",
            "url": "https://openai.com/index/openai-on-aws",
            "author": "",
            "published_at": "2026-04-28 00:00",
            "raw_summary": "OpenAI GPT models, Codex, and Managed Agents are now available on AWS.",
            "source_name": "OpenAI Blog",
            "source_url": "https://openai.com/blog/rss.xml",
            "domain": "ai",
            "lang": "en",
            "priority": 1,
        },
        {
            "title": "Atlas Obscura: The Forgotten Underground Rivers of London",
            "url": "https://www.atlasobscura.com/articles/underground-rivers-london",
            "author": "Sarah Durn",
            "published_at": "2026-04-27 14:30",
            "raw_summary": "Beneath the streets of London flow dozens of rivers that were gradually buried as the city expanded.",
            "source_name": "Atlas Obscura",
            "source_url": "https://www.atlasobscura.com/feeds/latest",
            "domain": "travel",
            "lang": "en",
            "priority": 1,
        },
    ]

    print("\n【第一步】抓取全文...")
    enriched = enrich_with_fulltext(test_articles, delay_seconds=1.0)

    print("\n【第二步】生成摘要...")
    results = summarize_all(enriched)

    if results:
        print("\n── 第一篇摘要完整输出 ──\n")
        for key, value in results[0].items():
            print(f"  {key}:")
            if isinstance(value, list):
                for item in value:
                    print(f"    - {item}")
            else:
                print(f"    {value}")
