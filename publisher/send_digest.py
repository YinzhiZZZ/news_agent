# publisher/send_digest.py
# 每日摘要推送：生成网页版 + 发送 HTML 邮件
#
# 输入：output/digest.json（已评分排序）
# 输出：output/digest_YYYY-MM-DD.html + Gmail 邮件推送

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import smtplib
import ssl
import re
from datetime import date
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from dotenv import load_dotenv
from config import DIGEST_CONFIG, USER_PROFILE

load_dotenv()

# ── 领域名称 → config key 映射 ─────────────────────────────────────────────────

_DOMAIN_NAME_TO_KEY = {
    info["name"]: key
    for key, info in USER_PROFILE["domains"].items()
}
# 兼容无空格写法（"AI与技术" vs "AI 与技术"）
_DOMAIN_NAME_TO_KEY.update({
    name.replace(" ", ""): key
    for name, key in list(_DOMAIN_NAME_TO_KEY.items())
})

# Claude 偶尔输出的同义变体 → 强制映射
_DOMAIN_ALIASES = {
    "ai":          ["ai", "人工智能", "技术", "tech"],
    "business":    ["商业", "互联网", "business", "企业"],
    "photography": ["摄影", "photo"],
    "travel":      ["旅游", "地理", "旅行", "travel"],
}

def _domain_key(article: dict) -> str:
    raw = article.get("domain", "")
    # 精确匹配
    if raw in _DOMAIN_NAME_TO_KEY:
        return _DOMAIN_NAME_TO_KEY[raw]
    no_space = raw.replace(" ", "")
    if no_space in _DOMAIN_NAME_TO_KEY:
        return _DOMAIN_NAME_TO_KEY[no_space]
    # 关键词模糊匹配
    raw_lower = raw.lower()
    for key, hints in _DOMAIN_ALIASES.items():
        if any(h in raw_lower for h in hints):
            return key
    return raw_lower


# ── 按 domain_quota 筛选文章 ───────────────────────────────────────────────────

def select_by_quota(articles: list[dict]) -> list[dict]:
    """
    按 DIGEST_CONFIG["domain_quota"] 每个领域取对应数量。
    优先保留 total_score 较高的文章；若无评分字段则保持原顺序。
    """
    quota = DIGEST_CONFIG.get("domain_quota", {})
    buckets: dict[str, list] = {k: [] for k in quota}

    for article in articles:
        key = _domain_key(article)
        if key in buckets:
            buckets[key].append(article)

    selected = []
    for domain_key, limit in quota.items():
        bucket = buckets.get(domain_key, [])
        # 有评分则按分排序，否则保持原顺序
        if bucket and "total_score" in bucket[0]:
            bucket.sort(key=lambda a: a["total_score"], reverse=True)
        selected.extend(bucket[:limit])

    return selected


# ── anchor 生成 ────────────────────────────────────────────────────────────────

def _anchor(index: int) -> str:
    return f"article-{index}"


# ── 网页版 HTML ────────────────────────────────────────────────────────────────

_DOMAIN_LABEL = {
    "ai":          "AI 与技术",
    "business":    "商业与互联网",
    "photography": "摄影",
    "travel":      "旅游与地理",
}

# 每个领域：主色、发光色、渐变、标签描述
_DOMAIN_THEME = {
    "ai": {
        "color":   "#00d4ff",
        "glow":    "rgba(0,212,255,0.35)",
        "grad":    "linear-gradient(135deg,#0d1117 0%,#0a0f1e 100%)",
        "border":  "#00d4ff",
        "tag_bg":  "rgba(0,212,255,0.12)",
        "tag_clr": "#00d4ff",
        "meta":    "#4a9eba",
        "text":    "#c9e8f0",
        "icon":    "⬡",
    },
    "photography": {
        "color":   "#4ade80",
        "glow":    "rgba(74,222,128,0.30)",
        "grad":    "linear-gradient(135deg,#0a1a0f 0%,#071210 100%)",
        "border":  "#4ade80",
        "tag_bg":  "rgba(74,222,128,0.12)",
        "tag_clr": "#4ade80",
        "meta":    "#4a8a5c",
        "text":    "#c6e8d0",
        "icon":    "◈",
    },
    "travel": {
        "color":   "#fbbf24",
        "glow":    "rgba(251,191,36,0.30)",
        "grad":    "linear-gradient(135deg,#1a1200 0%,#140e00 100%)",
        "border":  "#fbbf24",
        "tag_bg":  "rgba(251,191,36,0.12)",
        "tag_clr": "#fbbf24",
        "meta":    "#8a7020",
        "text":    "#f0e0b0",
        "icon":    "◎",
    },
    "business": {
        "color":   "#94a3b8",
        "glow":    "rgba(148,163,184,0.25)",
        "grad":    "linear-gradient(135deg,#0f1117 0%,#0c0e14 100%)",
        "border":  "#94a3b8",
        "tag_bg":  "rgba(148,163,184,0.10)",
        "tag_clr": "#94a3b8",
        "meta":    "#556070",
        "text":    "#c8d0da",
        "icon":    "◇",
    },
}
_DOMAIN_THEME_DEFAULT = _DOMAIN_THEME["business"]


def _score_bars(article: dict, theme: dict) -> str:
    """三维评分：横向进度条可视化"""
    if "total_score" not in article:
        return ""
    clr   = theme["color"]
    glow  = theme["glow"]
    dims  = [
        ("相关性", article.get("relevance", 0)),
        ("质量",   article.get("quality",   0)),
        ("新颖性", article.get("novelty",   0)),
    ]
    bars = ""
    for label, val in dims:
        pct = int(float(val) * 10)
        bars += f"""
        <div style="display:flex;align-items:center;gap:8px;margin-bottom:5px;">
          <span style="width:42px;font-size:11px;color:{theme['meta']};
              text-align:right;flex-shrink:0;">{label}</span>
          <div style="flex:1;height:4px;background:rgba(255,255,255,0.07);
              border-radius:2px;overflow:hidden;">
            <div style="width:{pct}%;height:100%;background:{clr};
                border-radius:2px;
                box-shadow:0 0 6px {glow};"></div>
          </div>
          <span style="width:24px;font-size:11px;color:{clr};
              font-family:monospace;flex-shrink:0;">{val}</span>
        </div>"""
    total = article["total_score"]
    total_color = clr if total >= 8 else "#fbbf24" if total >= 6.5 else "#6b7280"
    reason = article.get("score_reason", "")
    reason_html = (
        f'<p style="margin:6px 0 0;font-size:11px;color:{theme["meta"]};'
        f'line-height:1.5;font-style:italic;">{reason}</p>'
        if reason else ""
    )
    return f"""
      <div style="margin-top:16px;padding:12px 14px;
          background:rgba(255,255,255,0.03);border-radius:8px;
          border:1px solid rgba(255,255,255,0.06);">
        <div style="display:flex;justify-content:space-between;
            align-items:center;margin-bottom:8px;">
          <span style="font-size:11px;color:{theme['meta']};
              letter-spacing:.06em;text-transform:uppercase;">评分</span>
          <span style="font-size:18px;font-weight:800;color:{total_color};
              font-family:monospace;text-shadow:0 0 10px {total_color}88;">
            {total:.1f}</span>
        </div>
        {bars}
        {reason_html}
      </div>"""


def build_html_page(articles: list[dict], date_str: str, github_pages_url: str) -> str:
    cards = []
    for i, a in enumerate(articles):
        anchor = _anchor(i)
        dk     = _domain_key(a)
        label  = _DOMAIN_LABEL.get(dk, a.get("domain", ""))
        t      = _DOMAIN_THEME.get(dk, _DOMAIN_THEME_DEFAULT)

        topics_html = "".join(
            f'<span class="tag" style="background:{t["tag_bg"]};color:{t["tag_clr"]};'
            f'border:1px solid {t["tag_clr"]}33;">{topic}</span>'
            for topic in a.get("related_topics", [])
        )

        refs_html = ""
        if a.get("references"):
            items = "".join(
                (f'<li><a href="{r}" target="_blank" '
                 f'style="color:{t["color"]};word-break:break-all;">{r}</a></li>'
                 if r.startswith("http") else
                 f'<li style="color:{t["text"]};">{r}</li>')
                for r in a["references"]
            )
            refs_html = (
                f'<div class="refs">'
                f'<span style="color:{t["meta"]};font-size:11px;'
                f'text-transform:uppercase;letter-spacing:.06em;">参考文献</span>'
                f'<ul style="margin:6px 0 0;padding-left:16px;'
                f'font-size:12px;line-height:1.8;">{items}</ul></div>'
            )

        author = a.get("author", "未署名") or "未署名"
        bio    = a.get("author_bio", "")
        author_html = f'<span style="color:{t["color"]};">{author}</span>'
        if bio and bio not in ("暂无信息", ""):
            author_html += f' <span style="color:{t["meta"]};">· {bio}</span>'

        summary_clean = re.sub(r"<[^>]+>", "", a.get("summary", ""))
        score_html    = _score_bars(a, t)

        cards.append(f"""
    <article id="{anchor}" class="card" style="
        --clr:{t['color']};--glow:{t['glow']};
        background:{t['grad']};
        border:1px solid {t['color']}22;
        border-top:2px solid {t['color']};">
      <div class="card-meta">
        <span class="domain-badge" style="
            background:{t['tag_bg']};color:{t['color']};
            border:1px solid {t['color']}55;">
          {t['icon']} {label}
        </span>
        <span style="color:{t['meta']};font-size:12px;">
          {a.get('source_name','')} &nbsp;·&nbsp; {a.get('published_at','')}
        </span>
      </div>

      <h2 class="card-title">
        <a href="{a.get('source_url','#')}" target="_blank"
           style="color:#f0f4ff;">{a.get('main_topic','')}</a>
      </h2>

      <div style="font-size:12px;margin-bottom:12px;color:{t['meta']};">
        作者：{author_html}
      </div>

      <div class="tags">{topics_html}</div>

      <p style="margin:0 0 0;font-size:14px;color:{t['text']};
          line-height:1.85;">{summary_clean}</p>

      {refs_html}
      {score_html}
    </article>""")

    cards_html = "\n".join(cards)
    quota      = DIGEST_CONFIG.get("domain_quota", {})
    quota_desc = "  ".join(
        f'<span style="color:{_DOMAIN_THEME.get(k,_DOMAIN_THEME_DEFAULT)["color"]};">'
        f'{_DOMAIN_LABEL.get(k,k)} {v}</span>'
        for k, v in quota.items()
    )

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>每日资讯摘要 {date_str}</title>
<style>
  *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}

  body {{
    background: #06070d;
    color: #c8d0e0;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI",
                 "PingFang SC", "Hiragino Sans GB", "Noto Sans SC", sans-serif;
    min-height: 100vh;
    /* 细网格背景 */
    background-image:
      linear-gradient(rgba(255,255,255,.025) 1px, transparent 1px),
      linear-gradient(90deg, rgba(255,255,255,.025) 1px, transparent 1px);
    background-size: 40px 40px;
  }}

  .container {{
    max-width: 780px;
    margin: 0 auto;
    padding: 40px 16px 64px;
  }}

  /* ── Header ── */
  .site-header {{
    text-align: center;
    padding: 48px 0 40px;
    position: relative;
  }}
  .site-header::after {{
    content: '';
    display: block;
    width: 120px;
    height: 1px;
    background: linear-gradient(90deg, transparent, #00d4ff88, transparent);
    margin: 24px auto 0;
  }}
  .site-title {{
    font-size: clamp(22px, 5vw, 32px);
    font-weight: 900;
    letter-spacing: .04em;
    background: linear-gradient(90deg, #00d4ff, #a78bfa, #00d4ff);
    background-size: 200%;
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    animation: shimmer 4s linear infinite;
  }}
  @keyframes shimmer {{
    0%   {{ background-position: 0% }}
    100% {{ background-position: 200% }}
  }}
  .site-sub {{
    margin-top: 10px;
    font-size: 13px;
    color: #4a5568;
    font-family: monospace;
    letter-spacing: .08em;
  }}
  .quota-row {{
    margin-top: 12px;
    font-size: 12px;
    display: flex;
    justify-content: center;
    gap: 20px;
    flex-wrap: wrap;
  }}

  /* ── Card ── */
  .card {{
    border-radius: 14px;
    padding: 24px 26px 20px;
    margin-bottom: 20px;
    position: relative;
    overflow: hidden;
    transition: transform .22s ease, box-shadow .22s ease, border-color .22s ease;
    cursor: default;
  }}
  .card::before {{
    content: '';
    position: absolute;
    inset: 0;
    border-radius: inherit;
    opacity: 0;
    background: radial-gradient(600px circle at var(--mx,50%) var(--my,50%),
                  var(--glow) 0%, transparent 65%);
    transition: opacity .3s;
    pointer-events: none;
  }}
  .card:hover {{
    transform: translateY(-3px);
    box-shadow: 0 0 28px var(--glow), 0 8px 24px rgba(0,0,0,.5);
    border-color: var(--clr) !important;
  }}
  .card:hover::before {{ opacity: 1; }}

  .card-meta {{
    display: flex;
    align-items: center;
    flex-wrap: wrap;
    gap: 8px;
    margin-bottom: 12px;
  }}

  .domain-badge {{
    font-size: 11px;
    font-weight: 700;
    padding: 3px 10px;
    border-radius: 20px;
    letter-spacing: .04em;
    text-transform: uppercase;
  }}

  .card-title {{
    font-size: clamp(15px, 2.5vw, 18px);
    font-weight: 700;
    line-height: 1.45;
    margin-bottom: 10px;
  }}
  .card-title a {{
    text-decoration: none;
    transition: color .15s;
  }}
  .card-title a:hover {{ color: var(--clr) !important; }}

  /* ── Tags ── */
  .tags {{
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
    margin-bottom: 14px;
  }}
  .tag {{
    font-size: 11px;
    padding: 2px 9px;
    border-radius: 20px;
    letter-spacing: .02em;
  }}

  /* ── Refs ── */
  .refs {{
    margin-top: 14px;
    padding-top: 12px;
    border-top: 1px solid rgba(255,255,255,.06);
  }}

  /* ── Footer ── */
  .site-footer {{
    text-align: center;
    padding: 24px 0;
    font-size: 11px;
    color: #2a3040;
    font-family: monospace;
    letter-spacing: .06em;
  }}

  /* ── Responsive ── */
  @media (max-width: 600px) {{
    .card {{ padding: 18px 16px 16px; }}
    .card-title {{ font-size: 15px; }}
  }}
</style>
</head>
<body>
<div class="container">

  <header class="site-header">
    <h1 class="site-title">// 每日资讯摘要</h1>
    <p class="site-sub">DAILY DIGEST &nbsp;·&nbsp; {date_str} &nbsp;·&nbsp; {len(articles)} ARTICLES</p>
    <div class="quota-row">{quota_desc}</div>
  </header>

  {cards_html}

  <footer class="site-footer">
    GENERATED BY NEWS_AGENT &nbsp;·&nbsp; {date_str}
  </footer>

</div>
<script>
  // 鼠标跟踪：让每张卡片的光晕跟随鼠标
  document.querySelectorAll('.card').forEach(card => {{
    card.addEventListener('mousemove', e => {{
      const r = card.getBoundingClientRect();
      card.style.setProperty('--mx', (e.clientX - r.left) + 'px');
      card.style.setProperty('--my', (e.clientY - r.top)  + 'px');
    }});
  }});
</script>
</body>
</html>"""


# ── 邮件版 HTML ────────────────────────────────────────────────────────────────

def build_email_html(articles: list[dict], date_str: str, pages_url: str) -> str:
    rows = []
    for i, a in enumerate(articles):
        anchor = _anchor(i)
        dk = _domain_key(a)
        label = _DOMAIN_LABEL.get(dk, a.get("domain", ""))
        color = _DOMAIN_THEME.get(dk, _DOMAIN_THEME_DEFAULT)["color"]

        summary_clean = re.sub(r"<[^>]+>", "", a.get("summary", ""))
        first_sentence = re.split(r"[。！？.!?]", summary_clean)[0].strip()
        if first_sentence:
            first_sentence += "。"

        score_str = ""
        if "total_score" in a:
            score_str = f' &nbsp;<span style="color:{color};font-weight:700;">{a["total_score"]:.1f}分</span>'

        full_url = a.get("source_url", "#")

        rows.append(f"""
    <tr>
      <td style="padding:16px 20px;border-bottom:1px solid #f3f4f6;">
        <div style="margin-bottom:5px;">
          <span style="background:{color};color:#fff;font-size:11px;
              padding:1px 7px;border-radius:8px;">{label}</span>
          {score_str}
          <span style="color:#9ca3af;font-size:12px;margin-left:6px;">
            {a.get('source_name','')} · {a.get('published_at','')}
          </span>
        </div>
        <div style="font-size:16px;font-weight:700;color:#111827;
            margin-bottom:5px;line-height:1.4;">
          {a.get('main_topic','')}
        </div>
        <div style="font-size:14px;color:#374151;line-height:1.6;
            margin-bottom:8px;">
          {first_sentence}
        </div>
        <a href="{full_url}" style="font-size:13px;color:{color};
            font-weight:600;">阅读全文 →</a>
      </td>
    </tr>""")

    rows_html = "\n".join(rows)
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head><meta charset="UTF-8"></head>
<body style="margin:0;padding:0;background:#f9fafb;
    font-family:-apple-system,BlinkMacSystemFont,'Segoe UI','PingFang SC',sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0"
         style="background:#f9fafb;padding:24px 0;">
    <tr><td align="center">
      <table width="600" cellpadding="0" cellspacing="0"
             style="background:#fff;border-radius:12px;
             box-shadow:0 2px 8px rgba(0,0,0,.07);
             max-width:600px;width:100%;">
        <tr>
          <td style="padding:28px 20px 16px;text-align:center;
              border-bottom:2px solid #f3f4f6;">
            <h1 style="margin:0;font-size:22px;font-weight:800;
                color:#111827;">每日资讯摘要</h1>
            <p style="margin:6px 0 0;color:#6b7280;font-size:13px;">
              {date_str} · {len(articles)} 篇精选
            </p>
          </td>
        </tr>
        {rows_html}
        <tr>
          <td style="padding:16px 20px;text-align:center;
              font-size:12px;color:#9ca3af;">
            由 News Agent 自动生成 ·
            <a href="{pages_url}" style="color:#9ca3af;">查看完整网页版</a>
          </td>
        </tr>
      </table>
    </td></tr>
  </table>
</body>
</html>"""


# ── 发送邮件 ───────────────────────────────────────────────────────────────────

def send_email(subject: str, html_body: str) -> bool:
    sender    = os.getenv("GMAIL_SENDER")
    recipient = os.getenv("GMAIL_RECIPIENT")
    password  = os.getenv("GMAIL_APP_PASSWORD")

    if not all([sender, recipient, password]):
        print("[!] .env 缺少 GMAIL_SENDER / GMAIL_RECIPIENT / GMAIL_APP_PASSWORD，跳过发送")
        return False

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = sender
    msg["To"]      = recipient
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    try:
        ctx = ssl.create_default_context()
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=ctx) as server:
            server.login(sender, password)
            server.sendmail(sender, recipient, msg.as_bytes())
        print(f"邮件已发送 → {recipient}")
        return True
    except smtplib.SMTPAuthenticationError:
        print("[!] Gmail 认证失败：请确认 GMAIL_APP_PASSWORD 是应用专用密码")
        return False
    except Exception as e:
        print(f"[!] 邮件发送失败：{e}")
        return False


# ── 主函数 ─────────────────────────────────────────────────────────────────────

def publish(digest_path: str = None):
    # 路径默认值
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if digest_path is None:
        digest_path = os.path.join(root, "output", "digest.json")

    # 读取摘要
    print(f"读取：{digest_path}")
    with open(digest_path, encoding="utf-8") as f:
        data = json.load(f)
    all_articles = data.get("articles", [])
    print(f"共 {len(all_articles)} 篇文章")

    # 按领域配额筛选
    articles = select_by_quota(all_articles)
    print(f"配额筛选后：{len(articles)} 篇\n")

    date_str     = date.today().strftime("%Y-%m-%d")
    pages_url    = os.getenv("GITHUB_PAGES_URL", "")
    html_filename = f"digest_{date_str}.html"
    html_path     = os.path.join(root, "output", html_filename)

    # 生成 HTML
    page_html = build_html_page(articles, date_str, pages_url)

    # 保存带日期的归档版本
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(page_html)
    print(f"网页已生成 → {html_path}")

    # 同时写入 docs/index.html（GitHub Pages 入口）
    docs_path = os.path.join(root, "docs", "index.html")
    os.makedirs(os.path.dirname(docs_path), exist_ok=True)
    with open(docs_path, "w", encoding="utf-8") as f:
        f.write(page_html)
    print(f"GitHub Pages → {docs_path}")

    # 构建 GitHub Pages 完整 URL（供邮件链接使用）
    if pages_url:
        full_page_url = pages_url.rstrip("/")
    else:
        full_page_url = f"file:///{html_path.replace(os.sep, '/')}"
        print(f"[提示] 未设置 GITHUB_PAGES_URL，邮件链接将使用本地路径")

    # 生成并发送邮件
    email_html = build_email_html(articles, date_str, full_page_url)
    subject    = f"每日资讯摘要 {date_str}（{len(articles)} 篇）"
    send_email(subject, email_html)

    # 终端预览
    print(f"\n预览路径：")
    print(f"  归档版：{html_path}")
    print(f"  Pages : {docs_path}")
    if pages_url:
        print(f"  线上版：{full_page_url}")


if __name__ == "__main__":
    publish()
