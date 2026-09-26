# 本地单测（不联网），复用 SKILL 里的解析/还原逻辑
import re, urllib.parse

def extract_ddg_grab(html, n=10):
    out = []
    for m in re.finditer(
        r'<a[^>]*class="[^"]*result__a[^"]*"[^>]*href="([^"]+)"[^>]*>(.*?)</a>',
        html, re.S):
        title = re.sub(r"<.*?>", "", m.group(2)).strip()
        url = m.group(1).replace("&amp;", "&")
        um = re.search(r"[?&]uddg=([^&]+)", url)
        if um:
            url = urllib.parse.unquote(um.group(1))
        out.append({"title": title, "url": url})
    return out[:n]

def extract_bing_algo(html, n=10):
    out = []
    for blk in re.findall(r'<li class="b_algo".*?</li>', html, re.S):
        m = re.search(r'<h2[^>]*><a[^>]*href="([^"]+)"[^>]*>(.*?)</a>', blk, re.S)
        if not m:
            continue
        title = re.sub(r"<.*?>", "", m.group(2)).strip()
        url = m.group(1).replace("&amp;", "&")
        out.append({"title": title, "url": url})
    return out[:n]

def news_real_url(link):
    link = link.replace("&amp;", "&")
    m = re.search(r"[?&]url=([^&]+)", link)
    if not m:
        return link
    return urllib.parse.unquote(urllib.parse.unquote(m.group(1)))

def test_extract():
    html = '<a class="result__a" href="https://x.com/a">Sample Title</a>'
    r = extract_ddg_grab(html)
    assert r[0]["title"] == "Sample Title"
    assert r[0]["url"] == "https://x.com/a"
    print("test_extract OK")

def test_ddg_redirect_decode():
    html = ('<a class="result__a" href="//duckduckgo.com/l/?uddg='
            'https%3A%2F%2Fopenai.com%2F&amp;rut=x">Apple</a>')
    r = extract_ddg_grab(html)
    assert r[0]["url"] == "https://openai.com/"
    print("test_ddg_redirect_decode OK", r[0]["url"])

def test_bing_algo():
    html = ('<li class="b_algo"><h2><a href="https://bing.com/x?&amp;y=1">B Title</a></h2>'
            '<p class="b_lineclamp2">snippet here</p></li>')
    r = extract_bing_algo(html)
    assert r[0]["title"] == "B Title"
    assert r[0]["url"] == "https://bing.com/x?&y=1"
    print("test_bing_algo OK")

def test_news_re():
    xml = "<item><title>t1</title><link>l1</link></item>"
    assert re.search(r"<title>(.*?)</title>", xml).group(1) == "t1"
    print("test_news_re OK")

def test_news_apiclick_decode():
    link = ("http://www.bing.com/news/apiclick.aspx?ref=FexRss&amp;url="
            "https%3a%2f%2fwww.example.com%2f%25E6%2596%25B0%25E9%2597%25BB&amp;c=1")
    assert news_real_url(link) == "https://www.example.com/新闻"
    print("test_news_apiclick_decode OK", news_real_url(link))

if __name__ == "__main__":
    test_extract()
    test_ddg_redirect_decode()
    test_bing_algo()
    test_news_re()
    test_news_apiclick_decode()
    print("ALL TESTS PASSED")
