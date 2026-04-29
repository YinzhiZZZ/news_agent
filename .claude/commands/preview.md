在浏览器中打开今日最新的 digest HTML 文件。

步骤：

1. 列出 `output/` 目录下所有 `digest_*.html` 文件，找到日期最新的那个。

2. 用系统命令在默认浏览器打开：
   ```
   start output/digest_YYYY-MM-DD.html
   ```
   将 YYYY-MM-DD 替换为实际找到的最新文件名。

3. 打印文件路径和文件大小，以及文章数量（通过统计 HTML 中 `<article` 标签数量估算）。

4. 如果 `output/` 下没有任何 HTML 文件，提示用户先运行 `/run` 生成。
