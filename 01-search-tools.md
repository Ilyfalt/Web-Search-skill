# 可用搜索通道清单

实测确认可用的通道（Python 标准库 + 沙箱实测）。

## 1. DuckDuckGo HTML（首选，基本不被墙）

```
GET https://html.duckduckgo.com/html/?q=<query>
```
- 若 GET 返回 `202` 限制页 / 空结果：POST 同一 URL，body `q=<query>`（实测 POST 兜底可用）。
- 解析：`.result__a`（标题+链接）、`.result__snippet`（摘要）、`.result__url`。
- 链接是 `//duckduckgo.com/l/?uddg=<REAL>` 跳转包装，需还原（见 02）。

## 2. Bing 网页

```
GET https://www.bing.com/search?q=<query>&setlang=zh-Hans&mkt=zh-CN
```
- 注意：**数据中心 IP 偶发 JS 空壳**（有 `b_algo` 容器但无真实结果）。若抓到的是壳，该引擎记 note 即可，不影响其它引擎。
- 解析：`li.b_algo` → `h2 a` 标题 → `.b_caption p` 摘要。

## 3. Bing News RSS（几乎零被墙，最稳）

```
GET https://www.bing.com/news/search?q=<query>&format=rss
```
- **关键**：只带 `q` 和 `format=rss`，**不要加地区参数**（如 `mkt=zh-CN` / `cc=CN` / `setlang=zh-Hans`）——实测加了会返回 HTML 首页而不是 RSS。
- 返回标准 RSS 2.0：`<item>` 内含 `title`（标题）、`link`（apiclick 跳转）、`description`（摘要）、`pubDate`（时间）。
- `link` 形如 `http://www.bing.com/news/apiclick.aspx?ref=FexRss&...&url=<编码后的真实链接>`，需取 `url` 参数**双重 unquote** 还原真实外链（见 02）。
- 适合"最新消息""今日资讯"类查询；摘要短但够用。

## 4. 其它可选引擎（可能被墙，按需添加）

- **Mojeek**：`https://www.mojeek.com/search?q=<query>`（独立索引，无追踪；本沙箱实测 403，部分网络可用）
- **Brave Search / SearXNG 公共实例**：视网络环境而定，被 Cloudflare 拦截就跳过

## 5. 推荐封装（一次搜索全部使用）

```
search(query) -> {
   engine: "multi",
   engines: ["duckduckgo","bing","news"],
   note?: "duckduckgo: 5 条 | bing: 3 条 | news: 4 条",
   results: [ {title, url, snippet, engine} ]
}
```

三个引擎一起查，结果按 URL 合并去重（每条带 `engine` 来源字段）。某个引擎被反爬就把它记入 note，其余照常返回，绝不空手而归。

## 实践参数默认值

- `num_results` 默认 8-10 条（每引擎取 n 条再合并去重）
- `language` 默认 zh-CN
- 限速 `MIN_INTERVAL = 0.8s`
- 缓存 TTL 5 分钟（LRU）
