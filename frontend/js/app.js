(function () {
  window.addEventListener('alpine:init', () => {
    Alpine.store('auth', {
      token: localStorage.getItem('token') || null,
      user: JSON.parse(localStorage.getItem('user') || 'null'),

      get loggedIn() { return !!this.token },
      get username() { return this.user?.username || '' },
      get userId() { return this.user?.id || null },

      setToken(token) { this.token = token; if (token) localStorage.setItem('token', token); else localStorage.removeItem('token') },
      setUser(user) { this.user = user; if (user) localStorage.setItem('user', JSON.stringify(user)); else localStorage.removeItem('user') },

      logout() { this.setToken(null); this.setUser(null); window.location.href = '/screens/auth/login.html' },

      async fetchProfile() {
        if (!this.token) return;
        try {
          const res = await api('/api/users/me');
          if (res.ok) { this.setUser(await res.json()) }
        } catch (_) {}
      }
    })
  })

  window.api = async function (url, opts = {}) {
    const token = localStorage.getItem('token');
    const headers = { ...opts.headers, 'Content-Type': 'application/json' };
    if (token) headers['Authorization'] = 'Bearer ' + token;
    const res = await fetch(url, { ...opts, headers });
    if (res.status === 401 && !url.includes('/api/auth/')) {
      localStorage.removeItem('token'); localStorage.removeItem('user');
      const current = window.location.pathname;
      if (!current.includes('/auth/')) window.location.href = '/screens/auth/login.html?next=' + encodeURIComponent(current);
    }
    return res
  }
})();

document.addEventListener('DOMContentLoaded', function () {
  var saved = localStorage.getItem('theme');
  if (saved === 'dark') document.documentElement.setAttribute('data-theme', 'dark');
});
function toggleTheme() {
  var html = document.documentElement;
  var current = html.getAttribute('data-theme');
  var next = current === 'dark' ? 'light' : 'dark';
  html.setAttribute('data-theme', next);
  localStorage.setItem('theme', next);
}
function toggleMobileNav() {
  document.getElementById('mobileNav')?.classList.toggle('open');
}
