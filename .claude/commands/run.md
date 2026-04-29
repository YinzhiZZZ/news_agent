运行完整的 news_agent pipeline，按顺序执行以下步骤：

1. 运行 `pipeline.py`（fetch RSS → scrape 全文 → summarize 摘要 → 保存 digest.json）：
   ```
   PYTHONIOENCODING=utf-8 news_env/Scripts/python.exe pipeline.py
   ```

2. 运行 `processor/score_relevance.py`（对 digest.json 里的文章打分排序）：
   ```
   PYTHONIOENCODING=utf-8 news_env/Scripts/python.exe processor/score_relevance.py
   ```

3. 运行 `publisher/send_digest.py`（生成 HTML 网页 + 发送邮件）：
   ```
   PYTHONIOENCODING=utf-8 news_env/Scripts/python.exe publisher/send_digest.py
   ```

每一步完成后打印结果摘要，如果某步失败则停止并说明原因，不要继续执行后续步骤。
全部完成后输出今日摘要统计：采集篇数、入选篇数、HTML 路径、邮件是否发送成功。
