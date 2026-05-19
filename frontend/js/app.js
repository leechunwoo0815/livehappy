(function () {
  // 内嵌 SVG 占位图（无需外部网络请求）
  window.NO_IMAGE_URL = "data:image/svg+xml,%3Csvg xmlns=%27http://www.w3.org/2000/svg%27 width=%27800%27 height=%27600%27%3E%3Crect fill=%27%23e2e8f0%27 width=%27800%27 height=%27600%27/%3E%3Ctext fill=%27%2364748b%27 font-family=%27sans-serif%27 font-size=%2724%27 x=%2750%25%27 y=%2750%25%27 text-anchor=%27middle%27 dy=%27.3em%27%3E暂无图片%3C/text%3E%3C/svg%3E"

  // 立即注入样式：未登录时隐藏需要登录的链接
  var s = document.createElement('style')
  s.textContent = '[data-auth-required]{display:none!important}[data-logged-in="true"] [data-auth-required]{display:inline-flex!important}[data-logged-in="true"] .mobile-nav [data-auth-required]{display:block!important}'
  document.head.appendChild(s)

  window.getToken = function () { return localStorage.getItem('token') }
  window.getUser = function () { try { return JSON.parse(localStorage.getItem('user')) } catch (_) { return null } }
  window.setToken = function (t) { if (t) localStorage.setItem('token', t); else localStorage.removeItem('token') }
  window.setUser = function (u) { if (u) localStorage.setItem('user', JSON.stringify(u)); else localStorage.removeItem('user') }
  window.loggedIn = function () { return !!getToken() }

  window.logout = function () { setToken(null); setUser(null); window.location.href = '/screens/auth/login.html' }

  window.requireAuth = function () {
    if (!loggedIn()) {
      window.location.href = '/screens/auth/login.html?next=' + encodeURIComponent(window.location.href)
      return false
    }
    return true
  }

  window.renderNavAuth = function () {
    var user = getUser()
    var authed = user && getToken()
    document.body.dataset.loggedIn = authed ? 'true' : 'false'
    var profileUrl = '/screens/users/profile.html'
    var displayName = escapeHtml(user ? user.username || '' : '')
    if (authed && user.role === 'admin') {
      profileUrl = '/screens/admin/dashboard.html';
    }
    var loggedInHtml = '<div class="flex items-center gap-2">' +
      '<a href="' + profileUrl + '" class="btn btn-ghost btn-sm" style="text-decoration:none">' + displayName + '</a>' +
      '<a href="/screens/listings/create.html" class="btn btn-primary btn-sm">发布房源</a>' +
      '<button class="btn btn-outline btn-sm" onclick="logout()">退出</button>' +
      '</div>'
    var loggedOutHtml = '<a href="/screens/auth/login.html" class="btn btn-outline btn-sm">登录</a>' +
      '<a href="/screens/auth/register.html" class="btn btn-primary btn-sm">注册</a>'
    var html = authed ? loggedInHtml : loggedOutHtml
    document.querySelectorAll('[data-nav-auth]').forEach(function (el) { el.innerHTML = html })
    var mobileLoggedInHtml = '<div class="nav-actions" style="padding:var(--space-4)">' +
      '<a href="' + profileUrl + '" class="btn btn-outline w-full">' + displayName + '</a>' +
      '<a href="/screens/listings/create.html" class="btn btn-outline w-full" style="margin-top:var(--space-2)">发布房源</a>' +
      '<button class="btn btn-outline w-full" style="margin-top:var(--space-2)" onclick="logout()">退出</button>' +
      '</div>'
    var mobileLoggedOutHtml = '<div class="nav-actions" style="padding:var(--space-4)">' +
      '<a href="/screens/auth/login.html" class="btn btn-outline w-full">登录</a>' +
      '<a href="/screens/auth/register.html" class="btn btn-primary w-full" style="margin-top:var(--space-2)">注册</a>' +
      '</div>'
    document.querySelectorAll('[data-nav-auth-mobile]').forEach(function (el) { el.innerHTML = authed ? mobileLoggedInHtml : mobileLoggedOutHtml })
  }

  window.statusLabel = function (s) { return { pending: '待付款', paid: '已支付', confirmed: '已确认', cancelled: '已取消', completed: '已完成', refunded: '已退款', rejected: '已拒绝', approved: '已通过' }[s] || s }

  /* 将英文错误消息翻译为中文，确保用户永远看不到英文报错 */
  var _ERR_MAP = [
    [/Failed to fetch/i, '网络连接失败，请检查网络后重试'],
    [/NetworkError/i, '网络连接失败，请检查网络后重试'],
    [/Network request failed/i, '网络连接失败，请检查网络后重试'],
    [/Load failed/i, '加载失败，请检查网络后重试'],
    [/timeout/i, '请求超时，请稍后再试'],
    [/Request timed out/i, '请求超时，请稍后再试'],
    [/Unauthorized/i, '登录已过期，请重新登录'],
    [/Forbidden/i, '无权执行此操作'],
    [/Not Found/i, '请求的资源不存在'],
    [/Internal Server Error/i, '服务器开小差了，请稍后再试'],
    [/Bad Gateway/i, '服务器暂时不可用，请稍后再试'],
    [/Service Unavailable/i, '服务器暂时不可用，请稍后再试'],
    [/Conflict/i, '操作冲突，请刷新后重试'],
    [/Too Many Requests/i, '请求过于频繁，请稍后再试'],
    [/Validation/i, '数据格式不正确，请检查后重试'],
  ];
  window.translateError = function (msg) {
    if (!msg) return '操作失败，请稍后再试';
    for (var i = 0; i < _ERR_MAP.length; i++) {
      if (_ERR_MAP[i][0].test(msg)) return _ERR_MAP[i][1];
    }
    // 如果包含中文字符，直接返回原文（后端已翻译的中文消息）
    if (/[一-鿿]/.test(msg)) return msg;
    // 英文消息一律替换为通用中文提示
    return '操作失败，请稍后再试';
  }

  window.getCoverImage = function (listing) {
    if (listing.cover_image) return listing.cover_image
    if (listing.photos && listing.photos.length > 0) return listing.photos[0].url
    return NO_IMAGE_URL
  }

  window.escapeHtml = function (text) {
    if (text == null) return ''
    var d = document.createElement('div')
    d.textContent = String(text)
    return d.innerHTML
  }
})()

document.addEventListener('DOMContentLoaded', function () {
  renderNavAuth()
  var saved = localStorage.getItem('theme')
  if (saved === 'dark') document.documentElement.setAttribute('data-theme', 'dark')
})

function toggleTheme() {
  var html = document.documentElement
  var current = html.getAttribute('data-theme')
  var next = current === 'dark' ? 'light' : 'dark'
  html.setAttribute('data-theme', next)
  localStorage.setItem('theme', next)
}

function toggleMobileNav() {
  var el = document.getElementById('mobileNav')
  if (el) el.classList.toggle('open')
}
