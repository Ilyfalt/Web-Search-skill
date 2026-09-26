#!/usr/bin/env python3
"""gs.py —— 多引擎并行搜索。
用法: python3 gs.py "query" [n]
一次搜索同时查 duckduckgo + bing 网页 + bing_news(RSS)，合并去重后返回。
"""
import sys, time, re, urllib.request, urllib.parse

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/125.0 Safari/537.36")
_MIN = 0.8          # 限速：请求间隔（秒）
_last = [0.0]
_cache = {}

def _get(url, post=None, timeout=12):
    now = time.time()
    dt = _MIN - (now - _last[0])
    if dt > 0: time.sleep(dt)
    _last[0] = time.time()
    req = urllib.request.Request(url, headers={"User-Agent": UA,
                                               "Accept-Language": "zh-CN,zh;q=0.9"})
    if post:
        data = urllib.parse.urlencode(post).encode()
        req.add_header("Content-Type", "application/x-www-form-urlencoded")
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", "ignore")

def _q(q): return urllib.parse.quote(q)

# ---- 引擎 1: DuckDuckGo HTML（GET 失败则 POST 兜底） ----
def eng_ddg(q, n):
    def grab(html):
        out = []
        for m in re.finditer(
            r'<a[^>]*class="[^"]*result__a[^"]*"[^>]*href="([^"]+)"[^>]*>(.*?)</a>',
            html, re.S):
            title = re.sub(r"<.*?>", "", m.group(2)).strip()
            url = m.group(1).replace("&amp;", "&")
            # DDG 跳转链接 //duckduckgo.com/l/?uddg=REAL 还原成真实外链
            um = re.search(r"[?&]uddg=([^&]+)", url)
            if um:
                url = urllib.parse.unquote(um.group(1))
            out.append({"title": title, "url": url,
                        "snippet": "", "engine": "duckduckgo"})
        return out[:n]
    u = f"https://html.duckduckgo.com/html/?q={_q(q)}"
    results = grab(_get(u))
    if not results:  # GET 被限速/202，POST 兜底
        results = grab(_get(u, post={"q": q}))
    return results

# ---- 引擎 2: Bing 网页 ----
def eng_bing(q, n):
    u = f"https://www.bing.com/search?q={_q(q)}&setlang=zh-Hans&mkt=zh-CN"
    html = _get(u)
    out = []
    for blk in re.findall(r'<li class="b_algo".*?</li>', html, re.S):
        m = re.search(r'<h2[^>]*><a[^>]*href="([^"]+)"[^>]*>(.*?)</a>', blk, re.S)
        if not m:
            continue
        title = re.sub(r"<.*?>", "", m.group(2)).strip()
        url = m.group(1).replace("&amp;", "&")
        sn = re.search(r'<p[^>]*>(.*?)</p>', blk, re.S)
        snippet = re.sub(r"<.*?>", "", sn.group(1)).strip() if sn else ""
        out.append({"title": title, "url": url,
                    "snippet": snippet, "engine": "bing"})
    return out[:n]

# ---- 引擎 3: Bing News RSS（注意不要带地区参数，否则返回 HTML 首页） ----
def eng_news(q, n):
    u = f"https://www.bing.com/news/search?q={_q(q)}&format=rss"
    xml = _get(u)
    out = []
    for m in re.finditer(r"<item>(.*?)</item>", xml, re.S):
        it = m.group(1)
        t = re.search(r"<title>(.*?)</title>", it, re.S)
        l = re.search(r"<link>(.*?)</link>", it, re.S)
        if not (t and l):
            continue
        url = l.group(1).strip().replace("&amp;", "&")
        # Bing News apiclick 跳转链接还原（url 参数双重编码）
        um = re.search(r"[?&]url=([^&]+)", url)
        if um:
            url = urllib.parse.unquote(urllib.parse.unquote(um.group(1)))
        d = re.search(r"<description>(.*?)</description>", it, re.S)
        snippet = re.sub(r"<.*?>", "", d.group(1)).strip() if d else ""
        out.append({"title": t.group(1).strip(), "url": url,
                    "snippet": snippet, "engine": "news"})
    return out[:n]

# ---- 主入口：一次搜索同时使用全部引擎，合并去重 ----
def search(query, n=8):
    if query in _cache: return _cache[query]
    engines = [("duckduckgo", eng_ddg), ("bing", eng_bing), ("news", eng_news)]
    merged, notes = [], []
    for name, fn in engines:
        try:
            rows = fn(query, n)
            if rows:
                merged.extend(rows)
                notes.append(f"{name}: {len(rows)} 条")
            else:
                notes.append(f"{name}: 无结果")
        except Exception as e:
            notes.append(f"{name} 失败: {type(e).__name__}")
    # 按 URL 去重（保留首次出现的引擎来源）
    seen, deduped = set(), []
    for row in merged:
        key = row["url"].split("#")[0].rstrip("/")
        if key in seen:
            continue
        seen.add(key)
        deduped.append(row)
    # 按引擎轮转交错，保证前 n 条覆盖多个来源
    by_engine = {}
    for row in deduped:
        by_engine.setdefault(row["engine"], []).append(row)
    interleaved = []
    while any(by_engine.values()):
        for eng in sorted(by_engine):
            if by_engine[eng]:
                interleaved.append(by_engine[eng].pop(0))
    results = interleaved[:n]
    _cache[query] = {
        "engine": "multi",
        "engines": sorted({r["engine"] for r in results}),
        "note": " | ".join(notes),
        "results": results,
    }
    return _cache[query]

if __name__ == "__main__":
    q = sys.argv[1] if len(sys.argv) > 1 else "hello world"
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 8
    r = search(q, n)
    print("engines:", ",".join(r.get("engines", [])) or "none",
          "| note:", r.get("note", ""))
    for i, item in enumerate(r.get("results", []), 1):
        print(f"{i}. [{item['engine']}] {item['title']}\n   {item['url']}\n   {item['snippet'][:120]}")
