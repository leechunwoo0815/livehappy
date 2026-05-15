# 认证 API

## POST /auth/register

注册新用户。

```json
// Request
{"username": "test", "email": "test@test.com", "password": "Test1234!"}

// Response 200
{"access_token": "...", "refresh_token": "...", "token_type": "bearer"}

// Response 409
{"detail": "邮箱已注册"}
```

## POST /auth/login

用户登录。

```json
// Request
{"email": "test@test.com", "password": "Test1234!"}

// Response 200
{"access_token": "...", "refresh_token": "...", "token_type": "bearer"}

// Response 401
{"detail": "邮箱或密码错误"}
```

## POST /auth/refresh

刷新 Token。

```json
// Request
{"refresh_token": "..."}

// Response 200
{"access_token": "...", "refresh_token": "...", "token_type": "bearer"}
```

## 认证方式

所有受保护接口需要在 Header 中携带:

```
Authorization: Bearer <access_token>
```
