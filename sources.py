# sources.py
# 订阅源配置
#
# 分层说明：
#   TIER_1_RSS  —— 标准 RSS，直接可用，无需任何工具
#   TIER_2_RSSHUB —— 需要部署 RSSHub 后才能用（微信/微博/知乎/B站）
#
# 每个源的字段：
#   name     : 显示名称
#   url      : RSS feed 地址
#   domain   : 对应 config.py 里的领域
#   lang     : zh / en
#   priority : 1=高质量重点关注, 2=普通, 3=补充
#   note     : 备注（频率、特点等）

# ── Tier 1：标准 RSS，今天就能用 ───────────────────────────────────────────────

TIER_1_RSS = [

    # ── AI 与技术 ─────────────────────────────────────────────────────────────

    {
        "name": "OpenAI Blog",
        "url": "https://openai.com/blog/rss.xml",
        "domain": "ai", "lang": "en", "priority": 1,
        "note": "OpenAI 官方博客，模型发布和研究动态",
    },
    {
        "name": "Anthropic News",
        "url": "https://www.anthropic.com/news.rss",
        "domain": "ai", "lang": "en", "priority": 1,
        "note": "Anthropic 官方，Claude 相关动态",
    },
    {
        "name": "Google DeepMind Blog",
        "url": "https://deepmind.google/blog/rss.xml",
        "domain": "ai", "lang": "en", "priority": 1,
        "note": "Google AI 研究，Gemini 相关",
    },
    {
        "name": "The Verge — AI",
        "url": "https://www.theverge.com/ai-artificial-intelligence/rss/index.xml",
        "domain": "ai", "lang": "en", "priority": 1,
        "note": "科技媒体 AI 频道，产品向为主",
    },
    {
        "name": "MIT Technology Review — AI",
        "url": "https://www.technologyreview.com/topic/artificial-intelligence/feed/",
        "domain": "ai", "lang": "en", "priority": 1,
        "note": "MIT 技术评论，深度分析，质量高",
    },
    {
        "name": "机器之心",
        "url": "https://www.jiqizhixin.com/rss",
        "domain": "ai", "lang": "zh", "priority": 1,
        "note": "中文 AI 媒体，论文解读 + 行业动态",
    },
    {
        "name": "量子位",
        "url": "https://qbitai.com/rss",
        "domain": "ai", "lang": "zh", "priority": 1,
        "note": "中文 AI 媒体，产品和商业向偏多",
    },
    {
        "name": "arXiv — cs.AI",
        "url": "https://arxiv.org/rss/cs.AI",
        "domain": "ai", "lang": "en", "priority": 2,
        "note": "AI 学术论文，每日更新，量大，建议用关键词过滤",
    },
    {
        "name": "arXiv — cs.CV (计算机视觉)",
        "url": "https://arxiv.org/rss/cs.CV",
        "domain": "ai", "lang": "en", "priority": 3,
        "note": "计算机视觉论文，与摄影 AI 应用相关",
    },

    # ── 摄影 ──────────────────────────────────────────────────────────────────

    {
        "name": "DPReview",
        "url": "https://www.dpreview.com/feeds/news",
        "domain": "photography", "lang": "en", "priority": 1,
        "note": "摄影器材评测权威，相机和镜头资讯",
    },
    {
        "name": "PetaPixel",
        "url": "https://petapixel.com/feed/",
        "domain": "photography", "lang": "en", "priority": 1,
        "note": "摄影新闻 + 技巧，内容多元",
    },
    {
        "name": "The Phoblographer",
        "url": "https://www.thephoblographer.com/feed/",
        "domain": "photography", "lang": "en", "priority": 2,
        "note": "偏艺术和街头摄影，审美导向",
    },
    {
        "name": "Fstoppers",
        "url": "https://fstoppers.com/feed",
        "domain": "photography", "lang": "en", "priority": 2,
        "note": "摄影教程和商业摄影",
    },
    {
        "name": "1x.com Blog",
        "url": "https://1x.com/blog/rss.xml",
        "domain": "photography", "lang": "en", "priority": 2,
        "note": "艺术摄影社区，有摄影师访谈",
    },

    # ── 旅游与地理 ────────────────────────────────────────────────────────────

    {
        "name": "National Geographic — Travel",
        "url": "https://feeds.nationalgeographic.com/ng/travel/travel_main",
        "domain": "travel", "lang": "en", "priority": 1,
        "note": "国家地理旅行，自然和人文深度内容",
    },
    {
        "name": "BBC Travel",
        "url": "https://feeds.bbci.co.uk/travel/rss.xml",
        "domain": "travel", "lang": "en", "priority": 1,
        "note": "BBC 旅行频道，人文向强",
    },
    {
        "name": "Atlas Obscura",
        "url": "https://www.atlasobscura.com/feeds/latest",
        "domain": "travel", "lang": "en", "priority": 1,
        "note": "世界奇异地点发现，人文冷知识，强烈推荐",
    },
    {
        "name": "Lonely Planet News",
        "url": "https://www.lonelyplanet.com/articles/feed",
        "domain": "travel", "lang": "en", "priority": 2,
        "note": "旅行攻略和目的地推荐",
    },
    {
        "name": "穷游网 — 游记",
        "url": "https://bbs.qyer.com/feeds/",
        "domain": "travel", "lang": "zh", "priority": 2,
        "note": "中文游记，真实用户体验，需验证 URL",
    },

    # ── 商业与互联网 ──────────────────────────────────────────────────────────

    {
        "name": "36kr",
        "url": "https://36kr.com/feed",
        "domain": "business", "lang": "zh", "priority": 1,
        "note": "中文科技商业媒体，互联网公司动态",
    },
    {
        "name": "虎嗅",
        "url": "https://www.huxiu.com/rss/0.xml",
        "domain": "business", "lang": "zh", "priority": 1,
        "note": "深度商业分析，观点文章质量高",
    },
    {
        "name": "钛媒体",
        "url": "https://www.tmtpost.com/rss",
        "domain": "business", "lang": "zh", "priority": 2,
        "note": "科技创业，互联网公司报道",
    },
    {
        "name": "TechCrunch",
        "url": "https://techcrunch.com/feed/",
        "domain": "business", "lang": "en", "priority": 1,
        "note": "创业和科技公司动态，融资和并购信息",
    },
    {
        "name": "Stratechery",
        "url": "https://stratechery.com/feed/",
        "domain": "business", "lang": "en", "priority": 1,
        "note": "Ben Thompson 的深度科技商业分析，质量极高（部分付费）",
    },
    {
        "name": "Bloomberg Technology",
        "url": "https://feeds.bloomberg.com/technology/news.rss",
        "domain": "business", "lang": "en", "priority": 2,
        "note": "路透社科技新闻，数据较扎实",
    },
]


# ── Tier 2：需要 RSSHub，第二阶段接入 ─────────────────────────────────────────
# RSSHub 部署后，把下面的 {RSSHUB_BASE} 替换为你的实例地址
# 本地测试用：http://localhost:1200
# 也可用公共实例：https://rsshub.app（有请求限制，自建更稳定）

RSSHUB_BASE = "https://rsshub.app"  # 第二阶段替换为自建地址

TIER_2_RSSHUB = [

    # 微信公众号（需知道公众号 ID，格式示例）
    {
        "name": "少数派（微信）",
        "url": f"{RSSHUB_BASE}/wechat/mp/sspai",
        "domain": "ai", "lang": "zh", "priority": 2,
        "note": "少数派，科技数码，需确认公众号 ID",
    },

    # 知乎
    {
        "name": "知乎 — AI 话题",
        "url": f"{RSSHUB_BASE}/zhihu/topic/19550517",
        "domain": "ai", "lang": "zh", "priority": 2,
        "note": "知乎 AI 话题精华答案",
    },
    {
        "name": "知乎 — 摄影话题",
        "url": f"{RSSHUB_BASE}/zhihu/topic/19551828",
        "domain": "photography", "lang": "zh", "priority": 2,
        "note": "知乎摄影话题",
    },

    # 微博
    {
        "name": "微博 — 摄影超话",
        "url": f"{RSSHUB_BASE}/weibo/topic/摄影",
        "domain": "photography", "lang": "zh", "priority": 3,
        "note": "微博摄影讨论",
    },

    # B 站
    {
        "name": "B 站 — 摄影区",
        "url": f"{RSSHUB_BASE}/bilibili/ranking/region/163",
        "domain": "photography", "lang": "zh", "priority": 3,
        "note": "B 站摄影区热门视频（文字摘要意义有限）",
    },
]


# ── 辅助函数：获取指定领域的所有源 ────────────────────────────────────────────

def get_sources_by_domain(domain: str, tier: int = 1) -> list[dict]:
    """
    获取指定领域的订阅源列表
    domain: 'ai' / 'photography' / 'travel' / 'business' / 'all'
    tier:   1 = 仅 Tier 1, 2 = 包含 Tier 2
    """
    sources = TIER_1_RSS[:]
    if tier >= 2:
        sources += TIER_2_RSSHUB

    if domain == "all":
        return sources
    return [s for s in sources if s["domain"] == domain]


def get_priority_sources(max_priority: int = 1) -> list[dict]:
    """获取所有高优先级（priority <= max_priority）的源"""
    return [s for s in TIER_1_RSS if s["priority"] <= max_priority]
