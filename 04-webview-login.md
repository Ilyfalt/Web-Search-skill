# 用真实浏览器内核登录降风控（WebView）

搜索引擎对数据中心 IP 极易风控（DDG 202 / Bing 空壳）。真正降低风控、且获得**登录后的真实搜索结果**的办法：在真实浏览器内核（WebView / Chromium）里完成引擎账号登录，并把 cookie 全局持久化，之后搜索请求自动携带登录态。

以 Bing（微软账号）为例说明通用流程；思路同样适用于其它需要登录态的引擎。

## 适用场景

- 需要某引擎"真"的网页搜索结果（不是降级通道）。
- 需要较稳、较大量、持续一段时间的一批查询。
- 反爬严格且需要登录才能点亮结果。

## 关键点

1. **登录页**：在 WebView 打开引擎登录页（如 Bing：`https://login.live.com` 登录微软账号后访问 `https://www.bing.com` 自动携 cookie）。CookieManager 全局保存。
2. **登录检测**：注入 JS 轮询，检查页面出现退出入口 / 用户头像即视为已登录（选择器随引擎不同而变）。
3. **同意页/弹窗**：注入 JS 自动点同意按钮（如 `aria-label="同意"/"Agree"`）。
4. **搜索携态**：搜索 WebView 自动携带已存 cookie，直接走真实结果。

### JS 注入示例（登录态检测，通用版）

```js
// 每 2s 轮询；选择器按目标引擎调整
(function step(){
  var signedIn = !!document.querySelector(
    "a[href*='SignOut'], a[href*='logout'], [aria-label*='退出'], img[src*='avatar']"
  );
  AndroidBridge.onState("login", signedIn ? "yes" : "no");
  setTimeout(step, 2000);
})();
```

### 同意页自动点同意示例

```js
(function try(){
  var b = [...document.querySelectorAll("[aria-label]")]
            .find(x => /同意|Agree|Accept/i.test(x.getAttribute("aria-label")));
  if (b) b.click();
  setTimeout(try, 500);
})();
```

## 搜索结果提取（登录后）

```
onPageFinished → 注入 search_extract.js：
  每 600ms 轮询（最多 40 次）等 JS 渲染完成
  → 按 02 的解析规则提取结果（DDG/Bing 各自的选择器）
  → 若发现"验证码/此流量"字样标记 blocked
```

blocked 匹配时把 WebView z-index 浮到最上层，让用户手动过验证码（如：图片拼图 / reCAPTCHA），再继续抓取。

## 落地形态

- **桌面端**：无头 Chromium / Playwright / Selenium 保存 user-data-dir 与 cookie。
- **移动端 App**：WebView + CookieManager + 注入 JS。
- 注意合规：仅用于自己的搜索需求，不对抗验证码、不滥用账号。
