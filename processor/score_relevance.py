# processor/score_relevance.py
# 文章评分 Skill：相关性、质量、新颖性三维打分 + 去重
#
# 数据流：
#   summarize（结构化摘要列表）→ score_relevance（打分+去重）→ 排序后的精选列表

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import time
import re
from dotenv import load_dotenv
import anthropic
from config import USER_PROFILE, SCORING_WEIGHTS, MIN_SCORE_THRESHOLD

load_dotenv()
client = anthropic.Anthropic()

# ── 去重：Jaccard 相似度 ────────────────────────────────────────────────────────

def _tokenize(text: str) -> set:
    """把文本拆成词集合（中英文通用的简单分词）"""
    # 按非字母数字字符分割，保留中文字符和英文单词
    tokens = re.findall(r'[\u4e00-\u9fff]|[a-zA-Z0-9]+', text.lower())
    return set(tokens)


def _jaccard(set_a: set, set_b: set) -> float:
    if not set_a or not set_b:
        return 0.0
    return len(set_a & set_b) / len(set_a | set_b)


def deduplicate(articles: list[dict], threshold: float = 0.35) -> list[dict]:
    """
    用 Jaccard 相似度去除内容重复的文章。

    参数：
        articles  : 已打分（含 total_score）的文章列表
        threshold : Jaccard 相似度阈值，超过此值视为重复（默认 0.35）

    返回：
        去重后的文章列表（保留 total_score 较高的那篇）
    """
    # 预先计算每篇文章的词集合（main_topic + summary）
    token_sets = []
    for a in articles:
        text = a.get("main_topic", "") + " " + a.get("summary", "")
        token_sets.append(_tokenize(text))

    kept = []
    dropped = set()

    for i, article in enumerate(articles):
        if i in dropped:
            continue
        for j in range(i + 1, len(articles)):
            if j in dropped:
                continue
            sim = _jaccard(token_sets[i], token_sets[j])
            if sim >= threshold:
                # 保留分数较高的，丢弃另一篇
                score_i = article.get("total_score", 0)
                score_j = articles[j].get("total_score", 0)
                if score_i >= score_j:
                    dropped.add(j)
                else:
                    dropped.add(i)
                    break  # i 已被丢弃，不需要继续比较
        if i not in dropped:
            kept.append(article)

    removed = len(articles) - len(kept)
    if removed:
        print(f"去重：移除 {removed} 篇重复文章（Jaccard >= {threshold}）")

    return kept


# ── 单篇评分 ───────────────────────────────────────────────────────────────────

def score_article(article: dict, seen_topics: list[str]) -> dict | None:
    """
    调用 Claude API 对单篇文章进行三维评分。

    参数：
        article     : 摘要文章字典（含 summary、domain、main_topic 等字段）
        seen_topics : 本批次已处理文章的 main_topic 列表，用于判断新颖性

    返回：
        原始 article 字典 + relevance / quality / novelty / total_score 四个新字段
        失败时返回 None
    """
    domain = article.get("domain", "")
    keywords = []
    # 尝试从 USER_PROFILE 中匹配领域关键词
    for domain_key, domain_info in USER_PROFILE["domains"].items():
        if domain_info["name"] in domain or domain_key in domain.lower():
            keywords = domain_info["keywords"]
            break

    quality_pref = USER_PROFILE.get("quality_preference", "")
    exclude = USER_PROFILE.get("exclude_topics", [])

    seen_str = "、".join(seen_topics[-10:]) if seen_topics else "（无）"

    prompt = f"""你是一个资讯筛选助手。请对下面这篇文章从三个维度各打 0-10 分。

文章信息：
- 主题：{article.get('main_topic', '')}
- 来源：{article.get('source_name', '')}
- 发布时间：{article.get('published_at', '')}
- 领域：{domain}
- 摘要：{article.get('summary', '')}
- 相关话题：{', '.join(article.get('related_topics', []))}

评分标准：

1. relevance（相关性）0-10：
   - 领域关键词：{', '.join(keywords[:10]) if keywords else '见领域'}
   - 读者偏好：{quality_pref[:200]}
   - 排除话题（出现则降分）：{', '.join(exclude)}

2. quality（质量）0-10：
   - 有具体数据、技术细节、真实案例 → 高分
   - 纯公告、无内容支撑、标题党 → 低分

3. novelty（新颖性）0-10：
   - 本批次已出现的话题：{seen_str}
   - 与上述话题重复度高 → 低分
   - 提供全新视角、新事件、新数据 → 高分
   - 发布时间越近分数越高

请严格按照以下 JSON 格式返回，不要输出任何其他文字：
{{"relevance": 8, "quality": 7, "novelty": 6, "reason": "一句话说明评分理由"}}"""

    try:
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=200,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = response.content[0].text.strip()

        # 兼容 markdown 代码块包裹
        if raw.startswith("```"):
            raw = re.sub(r"```[a-z]*\n?", "", raw).strip("` \n")

        scores = json.loads(raw)

        relevance = float(scores.get("relevance", 5))
        quality   = float(scores.get("quality",   5))
        novelty   = float(scores.get("novelty",   5))

        total = (
            relevance * SCORING_WEIGHTS["relevance"]
            + quality * SCORING_WEIGHTS["quality"]
            + novelty * SCORING_WEIGHTS["novelty"]
        )

        result = dict(article)
        result["relevance"]   = round(relevance, 1)
        result["quality"]     = round(quality,   1)
        result["novelty"]     = round(novelty,   1)
        result["total_score"] = round(total,      2)
        result["score_reason"] = scores.get("reason", "")
        return result

    except json.JSONDecodeError:
        print(f"    [!] JSON 解析失败：{article.get('main_topic', '')[:40]}")
        return None
    except Exception as e:
        print(f"    [!] API 调用失败：{e}")
        return None


# ── 批量评分 ───────────────────────────────────────────────────────────────────

def score_all(articles: list[dict], delay_seconds: float = 0.3) -> list[dict]:
    """
    对文章列表批量打分，返回按 total_score 降序排列的结果。
    低于 MIN_SCORE_THRESHOLD 的文章会被过滤。
    """
    print(f"\n开始评分，共 {len(articles)} 篇")
    print("=" * 50)

    scored = []
    seen_topics = []

    for i, article in enumerate(articles, 1):
        topic = article.get("main_topic", article.get("title", ""))
        print(f"[{i}/{len(articles)}] {topic[:50]}...")

        result = score_article(article, seen_topics)
        if result:
            scored.append(result)
            seen_topics.append(topic)
            print(
                f"    相关性 {result['relevance']} | "
                f"质量 {result['quality']} | "
                f"新颖性 {result['novelty']} | "
                f"总分 {result['total_score']}"
            )
        if i < len(articles):
            time.sleep(delay_seconds)

    print("=" * 50)

    # 去重
    scored = deduplicate(scored)

    # 过滤低分
    before = len(scored)
    scored = [a for a in scored if a["total_score"] >= MIN_SCORE_THRESHOLD]
    filtered = before - len(scored)
    if filtered:
        print(f"过滤：移除 {filtered} 篇低分文章（< {MIN_SCORE_THRESHOLD}）")

    # 按总分降序排列
    scored.sort(key=lambda a: a["total_score"], reverse=True)

    print(f"\n评分完成：{len(scored)} 篇文章入选（原 {len(articles)} 篇）\n")
    return scored


# ── 直接运行：读取 digest.json 打分 ───────────────────────────────────────────
# python processor/score_relevance.py

if __name__ == "__main__":
    digest_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "output", "digest.json"
    )

    print(f"读取：{digest_path}")
    with open(digest_path, encoding="utf-8") as f:
        data = json.load(f)

    articles = data["articles"]
    print(f"共 {len(articles)} 篇文章\n")

    scored = score_all(articles)

    print("=" * 50)
    print("排序结果（总分从高到低）：")
    print("=" * 50)
    for rank, a in enumerate(scored, 1):
        print(
            f"#{rank:>2}  [{a['total_score']:>4.1f}]  "
            f"{a['main_topic'][:40]:<40}  "
            f"({a['source_name']})"
        )
        if a.get("score_reason"):
            print(f"      └─ {a['score_reason']}")
