/**
 * 统一 API 客户端，含自动 refresh token 和 BaseResponse 解包。
 *
 * 使用方式：
 *   apiClient.get('/bookings/')          → 自动解包 data.data
 *   apiClient.post('/auth/login', body)  → 返回 data.data
 *   apiClient.put('/listings/1', body)
 *   apiClient.delete('/listings/1')
 */
var apiClient = {
  baseUrl: '/api',

  _getHeaders: function () {
    var token = localStorage.getItem('token');
    var headers = { 'Content-Type': 'application/json' };
    if (token) headers['Authorization'] = 'Bearer ' + token;
    return headers;
  },

  _request: function (method, path, body) {
    var opts = { method: method, headers: this._getHeaders() };
    if (body) opts.body = JSON.stringify(body);

    var self = this;
    return fetch(this.baseUrl + path, opts).then(function (response) {
      // 401 → 尝试 refresh token → 重试一次
      if (response.status === 401 && path.indexOf('/auth/') === -1) {
        return self._refreshToken().then(function (refreshed) {
          if (refreshed) {
            opts.headers = self._getHeaders();
            return fetch(self.baseUrl + path, opts);
          }
          self._logout();
          throw new Error('登录已过期，请重新登录');
        });
      }
      return response;
    }).then(function (response) {
      return response.json().then(function (data) {
        // 统一 BaseResponse 解包
        if (typeof data.success === 'boolean') {
          if (!data.success) {
            throw new Error(data.message || '请求失败');
          }
          return data.data;
        }
        // 兼容旧格式（非 BaseResponse 的端点）
        return data;
      });
    }).catch(function (e) {
      if (e.message === '登录已过期，请重新登录') throw e;
      if (e.message && e.message !== '请求失败') throw e;
      throw new Error('网络错误');
    });
  },

  _refreshToken: function () {
    var refreshToken = localStorage.getItem('refresh_token');
    if (!refreshToken) return Promise.resolve(false);
    return fetch(this.baseUrl + '/auth/refresh', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh_token: refreshToken }),
    }).then(function (resp) {
      return resp.json();
    }).then(function (data) {
      if (data.success && data.data) {
        localStorage.setItem('token', data.data.access_token);
        return true;
      }
      if (data.access_token) {
        localStorage.setItem('token', data.access_token);
        return true;
      }
      return false;
    }).catch(function () {
      return false;
    });
  },

  _logout: function () {
    localStorage.removeItem('token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user');
    window.location.href = '/screens/auth/login.html';
  },

  get: function (path) { return this._request('GET', path); },
  post: function (path, body) { return this._request('POST', path, body); },
  put: function (path, body) { return this._request('PUT', path, body); },
  delete: function (path) { return this._request('DELETE', path); },
};
