# pipeline.py
# 完整流程入口：采集 -> 全文抓取 -> 摘要 -> 保存

import os
import json
from datetime import datetime

os.makedirs("output", exist_ok=True)

from collector.fetch_rss import fetch_all_sources
from collector.scrape_web import enrich_with_fulltext
from processor.summarize import summarize_all
from config import DIGEST_CONFIG


def run_pipeline(
    max_priority: int = 1,
    max_items_per_source: int = 5,
):
    run_at = datetime.now().strftime("%Y-%m-%d %H:%M")
    print(f"\n{'=' * 50}")
    print(f"新闻摘要 Pipeline — {run_at}")
    print(f"{'=' * 50}")

    # 第一步：采集 RSS
    articles = fetch_all_sources(
        max_priority=max_priority,
        max_items_per_source=max_items_per_source,
    )

    if not articles:
        print("\n未采集到任何文章，退出。")
        return

    # 第二步：补充全文（raw_summary > 200 字则跳过网络抓取）
    articles = enrich_with_fulltext(articles)

    # 第三步：按 DIGEST_CONFIG 限制数量后生成摘要
    max_articles = DIGEST_CONFIG.get("max_articles", 15)
    if len(articles) > max_articles:
        print(f"\n文章总数 {len(articles)} 超过上限 {max_articles}，截取前 {max_articles} 篇")
        articles = articles[:max_articles]

    summaries = summarize_all(articles)

    if not summaries:
        print("\n摘要生成失败，退出。")
        return

    # 第四步：打印第一篇摘要预览
    print("\n── 第一篇摘要预览 ──")
    first = summaries[0]
    for key, value in first.items():
        if isinstance(value, list):
            print(f"  {key}: {', '.join(value) if value else '—'}")
        else:
            print(f"  {key}: {value}")

    # 第五步：保存到 output/digest.json
    os.makedirs("output", exist_ok=True)
    output_path = os.path.join("output", "digest.json")
    payload = {
        "generated_at": run_at,
        "article_count": len(summaries),
        "articles": summaries,
    }
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    print(f"\n已保存 {len(summaries)} 篇摘要 -> {output_path}")


if __name__ == "__main__":
    run_pipeline()
