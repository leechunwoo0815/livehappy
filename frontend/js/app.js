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

  window.statusLabel = function (s) { return { pending: '待付款', paid: '已支付', confirmed: '已确认', cancelled: '已取消' }[s] || s }

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
