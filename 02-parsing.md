# 结果解析规则

从 DDG / Bing 的 HTML 与 RSS 里提取干净结果（标题/链接/摘要）。用 HTML/XML 解析（Python 用 BeautifulSoup 或正则，JS 用 cheerio/正则）。

## DuckDuckGo HTML 解析

- **标题+链接**：`a.result__a`（正则：`class="[^"]*result__a[^"]*"`，标题取标签内文本）
- **摘要**：`.result__snippet`
- **链接还原**：DDG 结果是 `//duckduckgo.com/l/?uddg=<REAL>&rut=...` 跳转包装 → 取 `uddg` 参数 URL 解码即真实外链。

```python
import re, urllib.parse

def real_url(href):
    href = href.replace("&amp;", "&")
    m = re.search(r"[?&]uddg=([^&]+)", href)
    return urllib.parse.unquote(m.group(1)) if m else href
```

## Bing 网页解析

- 结果容器：`li.b_algo`（先按块切分，再取块内字段）
- 标题：`h2 a`
- 摘要：`.b_caption p` 或 `.b_caption`
- 链接就是真实外链（无需还原），注意 `&amp;` → `&`

```python
for blk in re.findall(r'<li class="b_algo".*?</li>', html, re.S):
    m = re.search(r'<h2[^>]*><a[^>]*href="([^"]+)"[^>]*>(.*?)</a>', blk, re.S)
    if not m: continue
    title = re.sub(r"<.*?>", "", m.group(2)).strip()
    url = m.group(1).replace("&amp;", "&")
```

## Bing News RSS 解析

- 每 `<item>`：`title`（标题）、`description`（摘要）、`pubDate`（时间）、`link`（跳转）。
- **link 还原**：`apiclick.aspx?ref=FexRss&...&url=<双重编码>` → 取 `url` 参数**双重 unquote**：

```python
import re, urllib.parse

def news_url(link):
    link = link.replace("&amp;", "&")
    m = re.search(r"[?&]url=([^&]+)", link)
    if not m: return link
    return urllib.parse.unquote(urllib.parse.unquote(m.group(1)))  # 双重解码
```

- 中文 query 记得 `quote(query)`。
- `description` 内含 HTML 标签，去标签后当摘要。

## 汇总输出格式（给用户）

每一条按以下格式整理，附来源和序号：

```
1. **标题** (source · 时间)
   链接: url
   摘要: snippet（如足够）
```

最后给一个"小结"逐条解读，引用的条目用 [citation](url) 标注。
