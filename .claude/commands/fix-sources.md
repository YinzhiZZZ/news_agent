检查 `sources.py` 里所有订阅源的可用性，找出失败的并尝试修复或替换。

步骤：

1. 读取 `sources.py`，提取所有 TIER_1_RSS 源（暂不检查需要 RSSHub 的 Tier 2）。

2. 逐个用 feedparser 测试每个 URL，记录结果：
   ```
   PYTHONIOENCODING=utf-8 news_env/Scripts/python.exe -c "
   import feedparser, sys
   url = sys.argv[1]
   feed = feedparser.parse(url)
   ok = bool(feed.entries)
   print('OK' if ok else 'FAIL', len(feed.entries), url)
   " $URL
   ```
   每个源之间等待 0.5 秒，避免请求过快。

3. 汇总输出：
   - 正常的源（绿色 OK）
   - 失败的源（红色 FAIL），列出失败原因（超时 / XML 解析错误 / 无条目）

4. 针对每个失败的源：
   - 判断是临时网络问题（bozo 错误）还是永久失效（域名无法解析）
   - 如果是 XML 格式错误，检查该媒体是否有备用 RSS 地址（在 URL 上尝试常见变体：/feed、/rss、/feed.xml、/rss.xml）
   - 给出具体修复建议：替换 URL 或从列表中移除

5. 询问用户是否要自动应用修复建议，确认后更新 `sources.py`。
