# config.py
# 个人资讯 Agent —— 兴趣配置文件
# 这是整个系统的"产品需求文档"，所有 Agent 的行为以此为准

# ── 用户兴趣档案 ───────────────────────────────────────────────────────────────

USER_PROFILE = {
    "name": "Evangeline",

    # 四个关注领域，weight 影响排序权重（1.0 = 最高优先级）
    "domains": {
        "ai": {
            "name": "AI 与技术",
            "weight": 1.0,
            "keywords": [
                "AI", "大模型", "LLM", "Agent", "人工智能",
                "OpenAI", "Anthropic", "Claude", "GPT", "Gemini",
                "字节 AI", "豆包", "Kimi", "机器学习", "深度学习",
                "multimodal", "RAG", "fine-tuning", "inference",
            ],
            "preferred_content": "技术原理 + 产品应用并重，既要懂原理也要看落地案例",
        },
        "photography": {
            "name": "摄影",
            "weight": 0.8,
            "keywords": [
                "摄影", "相机", "镜头", "构图", "光线", "曝光",
                "后期", "修图", "Lightroom", "Photoshop", "胶片",
                "Sony", "Canon", "Nikon", "Fujifilm", "Leica",
                "street photography", "landscape", "portrait",
                "审美", "色彩", "摄影集", "摄影师",
            ],
            "preferred_content": "技术技巧和审美讨论均感兴趣，器材评测需有实拍样张",
        },
        "travel": {
            "name": "旅游与地理",
            "weight": 0.75,
            "keywords": [
                "旅行", "自然", "人文", "地理", "探索", "风光",
                "世界遗产", "徒步", "露营", "国家公园",
                "National Geographic", "BBC Travel", "人类学",
                "游记", "签证", "深度旅行", "小众目的地",
            ],
            "preferred_content": "偏好人文深度和自然科普，不喜欢攻略型流水账",
        },
        "business": {
            "name": "商业与互联网",
            "weight": 0.8,
            "keywords": [
                "字节跳动", "腾讯", "阿里", "百度", "Meta", "Google",
                "Apple", "Anthropic", "OpenAI", "商业模式", "互联网",
                "科技公司", "创业", "产品", "增长", "用户运营",
                "出海", "企业战略", "并购", "融资",
            ],
            "preferred_content": "企业动向和商业分析，有数据支撑的深度分析优先",
        },
    },

    # 全局排除：即便在关注领域内出现这些话题，也降低优先级
    "exclude_topics": [
        "体育赛事", "娱乐八卦", "明星", "股票行情",
        "房地产", "政治选举", "彩票", "医疗广告",
    ],

    # 内容质量偏好（会写进 score_relevance 的 Prompt）
    "quality_preference": (
        "有具体数据、真实案例或独特观点的深度内容。"
        "不喜欢标题党、内容农场和纯转载文章。"
        "对于 AI 话题，有技术细节或产品逻辑的优先；"
        "对于摄影，有实拍图例的优先；"
        "对于旅行，有真实体验的个人游记优先。"
    ),

    # 语言偏好
    "languages": ["zh", "en"],
}


# ── 摘要格式定义 ────────────────────────────────────────────────────────────────
# 这是你要求处理 Agent 输出的结构
# 每个字段对应你提出的格式需求

SUMMARY_FORMAT = {
    "source_name":  "信息来源媒体/网站名称",
    "source_url":   "原文链接",
    "author":       "作者姓名（无法确定则填 '未署名'）",
    "author_bio":   "作者简介：职位、擅长领域（从文中或公开信息推断，无法确定则填 '暂无信息'）",
    "published_at": "发布时间（格式：YYYY-MM-DD HH:MM）",
    "domain":       "所属领域（ai / photography / travel / business）",
    "main_topic":   "核心话题（一个简短短语，例如：'Claude 4 发布分析'）",
    "related_topics": ["相关话题标签，3–5 个"],
    "references":   ["文中引用的参考文献、报告或外部链接"],
    "summary":      "3–5 句话的内容总结：第一句点明核心事件，中间句补充关键数据或论据，最后句给出结论或影响",
}


# ── 评分权重 ────────────────────────────────────────────────────────────────────
# total_score = relevance×0.5 + quality×0.3 + novelty×0.2
# 三个维度均为 0–10 分

SCORING_WEIGHTS = {
    "relevance": 0.5,  # 与你兴趣领域的匹配程度
    "quality":   0.3,  # 内容深度、数据支撑、分析质量
    "novelty":   0.2,  # 是否提供新信息、新视角，而非重复已知内容
}

# 最低发布分数（低于此分数的文章直接过滤，不进入摘要）
MIN_SCORE_THRESHOLD = 5.0


# ── 每日摘要配置 ────────────────────────────────────────────────────────────────

DIGEST_CONFIG = {
    "max_articles":  8,               # 每天摘要最多收录几篇
    "run_hour":       8,              # 每天几点运行（24 小时制）
    "timezone":      "Asia/Shanghai",
    "output_format": "email",         # 目前先用 email，后续可改 dashboard
    "domain_quota": {                 # 各领域每日收录上限
        "ai":           3,
        "business":     3,
        "photography":  1,
        "travel":       1,
    },
}
