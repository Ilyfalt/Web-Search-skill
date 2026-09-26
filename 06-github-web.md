# GitHub 仓库信息抓取（绕过 API 匿名限流）

## 背景

GitHub REST API **匿名限流 60 次/小时/IP**，沙箱/脚本频繁查仓库信息很快撞 403 `rate limit exceeded`。但 `github.com` **网页端与 raw 文件不限流**，用标准库抓 HTML 即可拿到几乎全部仓库元数据——**无需令牌**。

## 三种方式对比

| 方式 | 限流 | 适用场景 |
|------|------|----------|
| ① GitHub 网页 HTML 抓取 | 无（注意频率礼貌） | 查 star/描述/homepage/topics/README、迁移检测，日常够用 |
| ② GitHub API + 令牌 | 5000 次/小时 | 大量结构化调用（批量建仓库、issues、CI 状态） |
| ③ git clone --depth 1 | 无 | 要完整文件树/历史时，重量级 |

## 抓取规则（实测稳定，2026-09）

请求仓库页：`GET https://github.com/{owner}/{repo}`（带浏览器 UA）。

| 字段 | 规则 |
|------|------|
| **star 数** | `aria-label="(\d+)\s+users? starred this repository"`（注意 `13.8k` 这类 k 后缀与逗号） |
| **描述** | `<meta name="description" content="([^"]*)">`（去掉 ` - owner/repo` 尾巴） |
| **官方 homepage** | react embedded JSON 里的 `"website":"([^"]*)"`（**最可靠**；README badge 链接会干扰"第一个 nofollow 链接"的土办法，别用那个） |
| **topics 标签** | `"topics":\[(.*?)\]` 内的所有 `"name":"..."` |
| **迁移检测** | 页面含 `This repository has been moved to <新位置>` |
| **404** | `urllib.error.HTTPError 404` → 仓库不存在 |

README 抓取：`GET https://raw.githubusercontent.com/{owner}/{repo}/{main|master}/README.md`（依次探测分支与大小写变体）。

## 直接可用的脚本

[gh.py](gh.py)（零第三方依赖）：

```bash
python3 gh.py withastro/astro              # star/描述/homepage/topics
python3 gh.py getzola/zola --readme        # 额外输出 README 前 500 字
python3 gh.py denoland/fresh               # 自动提示仓库是否迁移
```

## 注意事项

- 一定要带浏览器 UA，且**限速 ≥ 0.8s/次**、结果 LRU 缓存（和 gs.py 同一套反爬纪律）。
- 别高频轮询同一仓库（网页端虽不限流，但过猛会被临时风控）。
- GitHub 前端结构可能改版，若提取规则失效：先抓一页 HTML 看结构再调正则（本项目 06 就是为应对 API 限流 + 页面改版而写的）。
- 需要令牌的高频场景：用 Fine-grained token 只开最小权限，用完即撤销。
