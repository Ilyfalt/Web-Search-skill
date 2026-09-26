#!/usr/bin/env python3
"""gh.py —— GitHub 仓库信息查询（网页抓取，绕过 API 匿名限流）。
用法:
  python3 gh.py owner/repo            # 查 star/描述/homepage/迁移状态
  python3 gh.py owner/repo --readme   # 额外输出 README 全文（raw 抓取）
不依赖 GitHub API，因此不受匿名 60次/小时 限流影响。
"""
import sys, re, json, urllib.request

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/125.0 Safari/537.36")

def _get(url, timeout=15):
    req = urllib.request.Request(url, headers={"User-Agent": UA,
                                               "Accept-Language": "zh-CN,zh;q=0.9"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", "ignore")

def gh_info(full):
    """返回 dict：stars/description/homepage/moved/to，moved 表示仓库已迁移。"""
    html = _get(f"https://github.com/{full}")
    out = {"full_name": full}
    # 迁移检测
    m = re.search(r"This repository has been moved to\s*([^\s<]+)", html)
    if m:
        out["moved"] = True
        out["to"] = m.group(1).rstrip(".")
        return out
    # star 数（页面 aria-label 通常是完整数字，兼容 k/逗号写法）
    m = re.search(r'aria-label="([\d.,k]+)\s+users? starred this repository"', html)
    if m:
        raw = m.group(1).replace(",", "")
        if raw.endswith("k"):
            raw = str(int(float(raw[:-1]) * 1000))
        out["stars"] = raw
    # 描述
    m = re.search(r'<meta name="description" content="([^"]*)"', html)
    if m:
        out["description"] = m.group(1).split(" - ")[0].strip()
    # homepage / topics：从 react embedded JSON 的 sidebarAbout 提取（最可靠）
    m = re.search(r'"website"\s*:\s*"([^"]*)"', html)
    if m:
        out["homepage"] = m.group(1).replace("\\u0026", "&").replace("\\/", "/")
    m = re.search(r'"topics"\s*:\s*\[(.*?)\]', html)
    if m:
        topics = re.findall(r'"name"\s*:\s*"([^"]*)"', m.group(1))
        if topics:
            out["topics"] = topics
    return out

def gh_readme(full):
    """抓取 README（raw.githubusercontent.com，依次探测 main/master）。"""
    for branch in ("main", "master"):
        for name in ("README.md", "README.MD", "readme.md"):
            try:
                txt = _get(f"https://raw.githubusercontent.com/{full}/{branch}/{name}")
                if txt and "<!DOCTYPE" not in txt[:200]:
                    return txt
            except Exception:
                continue
    return ""

def fmt(info, readme=False):
    lines = [f"full_name: {info['full_name']}"]
    if info.get("moved"):
        lines.append(f"moved: True -> 新位置: {info.get('to')}")
    for k in ("stars", "description", "homepage", "topics"):
        if info.get(k):
            v = info[k]
            if isinstance(v, list):
                v = ", ".join(v)
            lines.append(f"{k}: {v}")
    if readme:
        r = gh_readme(info["full_name"])
        lines.append(f"readme_chars: {len(r)}")
        lines.append("--- README 前 500 字 ---")
        lines.append(r[:500])
    return "\n".join(lines)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    full = sys.argv[1].strip("/")
    readme = "--readme" in sys.argv[2:]
    try:
        info = gh_info(full)
        print(fmt(info, readme))
    except Exception as e:
        print(f"FAIL {type(e).__name__}: {e}")
        sys.exit(1)
