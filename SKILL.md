---
name: web-search
description: 用多引擎获取信息的能力包：DuckDuckGo 网页、Bing 网页、Bing News RSS 一次并行搜索并合并结果，附带反封禁、GitHub 网页抓取（绕过 API 匿名限流）、浏览器登录降风控。执行"搜索 X / 用搜索引擎搜一下 / 搜索并给我信息 / 查 GitHub 仓库信息"这类任务时使用。
---

# 网页搜索 Web Search

用搜索引擎获取信息并给用户可读的结论。核心方法论 + 实测可用的工具/接口 + 多引擎并行策略。

## 文件索引

| 文件 | 内容 | 何时读 |
|------|------|--------|
| [01-search-tools.md](01-search-tools.md) | 可用搜索通道清单（DDG / Bing / Bing News RSS） | 一开始，选通道 |
| [02-parsing.md](02-parsing.md) | 结果解析规则：标题/链接还原/摘要 | 解析结果时 |
| [03-anti-block.md](03-anti-block.md) | 被墙诊断、多引擎策略、UA 轮换、限速、缓存 | 被拦截/结果异常时 |
| [04-webview-login.md](04-webview-login.md) | 用真实浏览器内核登录降风控（WebView + cookie 持久化） | 需要登录态/大量搜索时 |
| [05-cli-script.md](05-cli-script.md) | 可直接跑的 CLI/脚本骨架（Python 标准库） | 要自动化抓取时 |
| [06-github-web.md](06-github-web.md) | GitHub 网页抓取（绕过 API 匿名限流，无需令牌） | 查 GitHub 仓库信息时 |
| [gs.py](gs.py) | 实测可用的多引擎并行 CLI（DDG + Bing + News） | 直接跑 |
| [gh.py](gh.py) | 零依赖 GitHub 仓库信息查询 CLI（网页抓取） | 直接跑 |

## 快速上手（30 秒版）

执行一次搜索 + 给出条理结论的最快路径：

1. **一次搜索同时查所有引擎**：DuckDuckGo（`html.duckduckgo.com/html/`）+ Bing 网页 + Bing News RSS，合并去重
2. 每个引擎独立 try/except：某个引擎被墙只影响它自己的来源，其余照常返回
3. 解析出 标题/链接/摘要（带引擎来源标注），别贴原始 HTML

```python
# 最小可用：Bing News RSS（几乎不被墙，最稳）
import urllib.request, urllib.parse
q = urllib.parse.quote("关键词")
url = f"https://www.bing.com/news/search?q={q}&format=rss"
xml = urllib.request.urlopen(url, timeout=12).read().decode("utf-8", "ignore")
# 每条: title / link / pubDate / description
```

或直接用 [gs.py](gs.py)：`python3 gs.py "关键词" [条数]`，一次并行查全部引擎并合并结果。

查 GitHub 仓库信息（star/描述/homepage/topics/README）：`python3 gh.py owner/repo [--readme]`，网页抓取不走 API，**不受匿名限流影响，无需令牌**（见 [06](06-github-web.md)）。

## 最核心的经验

1. **搜索引擎网页端对数据中心 IP 常返回风控页**：DDG 偶发 202 限制页、Bing 偶发 JS 空壳——这是网络层风控，不是代码错
2. **一定有能用的通道**：Bing News RSS（`format=rss` 且**不要带地区参数**）基本不被墙，**先跑通一条**再优化
3. **多引擎并行是常态**：一次搜索全部引擎一起上，按 URL 合并去重；单个引擎被墙只记 note，不影响整体结果
4. **跳转链接要还原**：DDG 的 `//duckduckgo.com/l/?uddg=`、Bing News 的 `apiclick.aspx?url=` 都要解码成真实外链，否则链接没法直接用
5. **反爬三件套**：UA 轮换、限速 ≥ 0.8s/次、LRU 缓存
6. **真想高频+高质搜索**：用真实浏览器内核（WebView/无头 Chrome）登录引擎账号，缓存 cookie 全局持久化（见 04）

## 标准搜索流程

```
1. 明确查询：把用户的话转成 query + 语言 + 条数
2. 通道：duckduckgo + bing + news 一起查（gs.py 已封装）
3. 请求：加 UA、限速≥0.8s/次、本地缓存
4. 解析：标题/还原 URL/摘要/来源时间，标注引擎来源
5. 合并：按 URL 去重，各引擎失败的记入 note
6. 汇总：按来源/时间整理带引用的结论给用户
```

## 环境限制备忘

- 沙箱请求可能 401/403（本环境实测 Mojeek 403）：**换通道往往比改 header 有用**
- 分类测试 → 单测 → 再整链路（详见 05 脚本与测试）
- 把 skill 当"教学包"，快的验证用 QuickJS（eval_javascript）本地解析
