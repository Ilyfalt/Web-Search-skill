# 反被封禁 / 多引擎策略

## 被墙诊断

数据中心 IP 访问搜索引擎网页端，常见的风控表现：

- **DuckDuckGo**：返回 `202` 限制页 / 空结果
- **Bing 网页**：JS 空壳（有 `b_algo` div 但无真实结果）或直接跳首页
- **Bing News RSS**：本应返回 XML，却返回 HTML 首页（通常是**带了地区参数**所致，见 01）

**判断结论**：这不是代码错，是网络层风控。别浪费时间改 header / 加 cookie 去解——某个引擎被墙就跳过它，其余引擎继续，必要时上登录（04）。

## 多引擎策略（核心）

```
一次搜索同时查：duckduckgo(html) + bing(网页) + bing_news(RSS)
```

- 每个引擎独立 try/except：被墙/空结果只影响该引擎来源，记入 note 后继续。
- 结果按 URL 合并去重，每条保留 `engine` 来源字段，方便用户看到出处。
- `news` 基本总能返回东西，作为天然保底。

## 反爬三件套（任何引擎都以礼相待）

1. **UA 轮换**：模拟真实浏览器 UA（Chrome/Edge/Safari on Windows/macOS/Android），避免被当 bot。
2. **限速**：每次请求间隔 ≥ 0.8s（MIN_INTERVAL）。
3. **缓存**：结果 LRU 缓存，TTL 5 分钟；同类 query 不重复打。

## 常见拦/解一览

| 现象 | 原因 | 修法 |
|------|------|------|
| 全 401 / "请求参数不完整" | 可能网关缺 header | 先测不存在路径区分；补齐 UA 等 |
| DDG GET 空 / 202 | Rate limit | 改 POST `html.duckduckgo.com/html/` |
| Bing 网页空壳 | IP 风控 | 该引擎记 note，靠 DDG/News 补 |
| Bing News 返回 HTML 而非 RSS | 带了地区参数 | 只保留 `q` + `format=rss` |
| Mojeek 403 | 风控 | 跳过，不加入默认引擎列表 |

## TLS 指纹

- 沙箱/命令行 requests/curl 可能被更严的 TLS 指纹识别。若网站极严：
  - 用浏览器内核（WebView/Playwright/无头 Chrome）而非裸 HTTP。
  - 注意：**结果已取到但正文打不开 vs 被墙**要区分——Record note 说明"结果已取到但爬取受到限制"。

## 状态与节流好习惯

- 每个引擎独立 try/except；某引擎本次失败后，同一次搜索不再重试该引擎。
- 输出里给 `engine:` 字段，方便用户看到来源。
- 不要多线程打同一域名过猛，会被临时封 IP。

## 何时上 WebView 登录（04）

启用到"需要真实网页搜索结果、登录态、大量连续查询"时才用。单次低量查询走多引擎并行就够了。
