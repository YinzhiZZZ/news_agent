引导用户把一个新 RSS 订阅源添加到 `sources.py`。

按以下步骤操作：

1. 先读取 `sources.py`，了解现有源的格式和已有哪些源。

2. 向用户提问（一次问完，不要分多轮）：
   - RSS feed URL 是什么？
   - 来源名称（source name）？
   - 属于哪个领域？可选：ai / photography / travel / business
   - 内容语言？可选：zh / en
   - 优先级？1 = 高优先级直接采集，2 = 需要 RSSHub

3. 用 curl 或 feedparser 验证该 URL 是否可以正常解析，打印前 3 条文章标题确认内容符合预期。
   验证命令：
   ```
   PYTHONIOENCODING=utf-8 news_env/Scripts/python.exe -c "
   import feedparser
   feed = feedparser.parse('$URL')
   print(f'状态：{\"成功\" if feed.entries else \"失败\"}，共 {len(feed.entries)} 篇')
   for e in feed.entries[:3]:
       print(' -', e.get('title','无标题'))
   "
   ```

4. 验证通过后，将新源按格式添加到 `sources.py` 对应的 TIER_1_RSS 或 TIER_2_RSSHUB 列表末尾。

5. 打印添加后的完整条目，让用户确认格式正确。
