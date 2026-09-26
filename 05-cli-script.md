# 可直接跑的 CLI/脚本骨架

提供一个可运行的多引擎并行搜索脚本（Python，标准库实现），开箱即用。

## gs.py —— 多引擎并行搜索（零第三方依赖）

文件：[gs.py](gs.py)（与本目录下实际脚本同步）。

- **一次搜索同时查全部引擎**：`duckduckgo(html) + bing(网页) + bing_news(RSS)`，按 URL 合并去重
- 每条结果带 `engine` 来源字段；单引擎被墙只记 note，不影响整体
- 跳转链接自动还原（DDG `uddg=` / Bing News `apiclick url=` 双重解码）
- 内置 UA、限速（0.8s）、LRU 缓存、每引擎独立 try/except
- 用法：`python3 gs.py "关键词" [条数]`，默认每引擎取 8 条合并

```bash
python3 gs.py "OpenAI 最新消息" 5
# engines: bing,duckduckgo,news | note: duckduckgo: 5 条 | bing: 5 条 | news: 5 条
# 1. [duckduckgo] 标题
#    链接
#    摘要
```

> 说明：**Bing News RSS（`format=rss`，不带地区参数）最稳**，基本总能出结果；DDG/Bing 网页视 IP 风控情况可能被墙，脚本会把它记入 note，其余引擎照常返回。生产版建议 requests + beautifulsoup，并开启 03 的限速与 LRU 缓存。

## gh.py —— GitHub 仓库信息查询（网页抓取，绕过 API 匿名限流）

文件：[gh.py](gh.py)。用 `github.com` 网页 + `raw.githubusercontent.com` 抓取，**不依赖 GitHub API，不受 60 次/小时 匿名限流影响，无需令牌**。详见 [06-github-web.md](06-github-web.md)。

```bash
python3 gh.py withastro/astro        # star / 描述 / homepage / topics
python3 gh.py getzola/zola --readme  # 额外输出 README 前 500 字
python3 gh.py denoland/fresh         # 仓库迁移时自动提示新位置
```

> 说明：GitHub 前端结构可能改版，若提取规则失效按 06 的规则先抓一页 HTML 看结构再调正则。

## 单元测试（不联网）

文件：[tests_gs.py](tests_gs.py)。本地跑：

```bash
python3 tests_gs.py
```

联网冒烟测试：

```bash
python3 gs.py "测试"
```

## 使用建议

1. 先跑通一条通道（DDG）→ 再补 Bing / Bing News。
2. 单次低量查询：`python3 gs.py "关键词"` 即可。
3. 需要登录态 / 真实 Web 结果：参考 04 WebView 登录。
4. 记得给结果带来源与引注，别把原始 HTML 丢给用户。
