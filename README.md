# Web-Search-skill

网页搜索能力包（Web Search Skill）：用 DuckDuckGo + Bing + Bing News RSS 一次并行搜索并合并结果，附带反封禁策略、GitHub 网页抓取（绕过 API 匿名限流）、WebView 登录降风控，以及零第三方依赖的 CLI 脚本。

## 内容

| 文件 | 内容 |
|------|------|
| SKILL.md | Skill 元数据与快速上手 |
| 01-search-tools.md | 可用搜索通道清单 |
| 02-parsing.md | 结果解析规则（跳转链接还原） |
| 03-anti-block.md | 反封禁与多引擎策略 |
| 04-webview-login.md | WebView 登录降风控 |
| 05-cli-script.md | CLI 脚本说明 |
| 06-github-web.md | GitHub 网页抓取（绕过 API 匿名限流） |
| gs.py | 零依赖 CLI 搜索脚本（多引擎并行） |
| gh.py | 零依赖 GitHub 仓库信息查询脚本 |
| tests_gs.py | 单元测试 |

## 能力

- 一次搜索**同时使用全部引擎**：DuckDuckGo 网页 + Bing 网页 + Bing News RSS
- 结果按 URL 合并去重，每条带 `engine` 来源标注
- 单个引擎被墙/被限速只记 note，其余引擎照常返回，绝不空手而归
- 跳转链接自动还原（DDG `uddg=` / Bing News `apiclick url=` 双重解码）
- **GitHub 仓库信息网页抓取**：star / 描述 / homepage / topics / README，不受 API 匿名限流影响、无需令牌
- 反爬三件套：UA 轮换、限速（≥0.8s/次）、LRU 缓存
- WebView 登录降风控（cookie 持久化）

## 必要安装

- **Python 3**（只用标准库，无需 pip 安装任何第三方包）
- 把整个目录复制到你的 skills 目录即可，例如：

```bash
# 如果你的技能目录是 /skills
mkdir -p /skills/web-search
cp SKILL.md 0*.md gs.py tests_gs.py /skills/web-search/
```

## 用法

### CLI 直接跑

```bash
# 多引擎并行搜索
python3 gs.py "关键词" [条数]

# 查 GitHub 仓库信息（免 API 限流、无需令牌）
python3 gh.py owner/repo [--readme]

# 示例：
python3 gs.py "OpenAI 最新消息" 5
python3 gh.py withastro/astro
```

输出格式：每行 `序号. [引擎来源] 标题`，下面跟链接和摘要，并汇总各引擎命中的条数。

### 作为 AI Skill 使用

把目录放到 skills 目录后，AI 在收到"搜索 X / 用搜索引擎搜一下 / 搜索并给我信息"这类任务时会自动调用本 skill 的通道与解析规则。

### 单元测试

```bash
python3 tests_gs.py
```

## GitHub 抓取说明

`gh.py` 用 `github.com` 网页 + `raw.githubusercontent.com` 抓取仓库信息（star/描述/homepage/topics/README），**不依赖 GitHub API**，因此不受匿名 60 次/小时限流影响、**无需令牌**。GitHub 前端改版时按 `06-github-web.md` 的规则重新抓一页 HTML 调整正则即可。

## 引擎备注

- **Bing News RSS 最稳**：`https://www.bing.com/news/search?q=<query>&format=rss`，注意**不要带地区参数**（`mkt`/`cc`/`setlang`），否则会返回 HTML 首页而不是 RSS。
- 可选引擎（按需添加）：Mojeek（`https://www.mojeek.com/search?q=<query>`）、Brave / SearXNG 公共实例，部分网络环境可能被风控。

## 许可证

[MIT](LICENSE)
