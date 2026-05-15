# GitHub Actions CI 日志结构分析

> **工作流**: Python CI  
> **触发**: push to develop (commit `82ae0f4`)  
> **状态**: ✅ success  
> **运行时间**: 2026-05-15, 耗时 ~28 秒  
> **完整日志**: 439 行, 66 KB

---

## 日志结构总览

每条日志格式: `Job名称\t步骤名称\t时间戳\t内容`

```
Lint & Test	Set up job	2026-05-15T09:03:22.678Z ##[group]Runner Image Provisioner
Lint & Test	Run actions/checkout@v4	2026-05-15T09:03:23.546Z ##[group]Run actions/checkout@v4
...
```

> 日志按 `Tab` 分隔，共 4 列: `Job` / `Step` / `Timestamp` / `Message`

---

## 各步骤详解

### 1. Set up job — 环境初始化 (L1-L32)

```
Runner Image: ubuntu-24.04
GitHub Token Permissions: Contents/Metadata/Packages = read
Worker ID: {d66a3c3a-...}
```

**关键信息**:
- 操作系统: Ubuntu 24.04.4 LTS
- Runner: GitHub Actions 托管 (Azure eastus)
- GITHUB_TOKEN 只有读权限

### 2. Run actions/checkout@v4 — 拉取代码 (L33-L104)

```
参数:
  repository: leechunwoo0815/livehappy
  fetch-depth: 1       ← 浅克隆, 只拉最新 commit
  persist-credentials: true

流程:
  1. git init /home/runner/work/livehappy/livehappy
  2. git remote add origin https://github.com/...
  3. git fetch --depth=1 origin +82ae0f4:refs/remotes/origin/develop
  4. git checkout --progress --force -B develop refs/remotes/origin/develop
```

**关键信息**:
- 工作目录: `/home/runner/work/livehappy/livehappy`
- 使用 Token 认证 (非 SSH)

### 3. Run actions/setup-python@v5 — 安装 Python (L105-L125)

```
Python 3.12.13 (CPython)
pip cache: 66 MB, 命中的缓存 key: setup-python-Linux-x64-24.04-...
```

**关键信息**:
- pip 缓存恢复成功 (第二次运行起节省 ~10s)
- Python 路径: `/opt/hostedtoolcache/Python/3.12.13/x64`

### 4. Install dependencies — 安装依赖 (L126-L384)

```
pip install -e ".[dev]"

构建 livehappy (pyproject.toml editable install)
安装 79 个包:
  - fastapi, uvicorn, sqlalchemy, asyncpg  (生产依赖)
  - pytest, pytest-asyncio, ruff, mypy     (开发依赖)
  - aiosqlite                                (测试数据库)
```

**关键信息**:
- 安装 79 个 Python 包
- 耗时 ~15 秒 (首次 ~40 秒)
- 编译了本地包 `livehappy-0.1.0`

### 5. Ruff check — 代码检查 (L385-L396)

```
ruff check backend/
→ All checks passed!
```

**关键信息**:
- 0 错误, 0 警告
- 配置: pyproject.toml 中 select+ignore

### 6. Ruff format check — 格式检查 (L397-L408)

```
ruff format --check backend/
→ 47 files already formatted
```

**关键信息**:
- 47 个文件格式正确

### 7. Test — 单元测试 (L409-L421)

```
PYTHONPATH=backend pytest backend/ -q
→ ............... (15 passed in 6.19s)
```

**关键信息**:
- 15 个测试全部通过
- 测试数据库: SQLite + aiosqlite (CI 无需启动 PostgreSQL)
- 耗时 6.19 秒

### 8. Post Run — 清理 (L422-L439)

```
Post job cleanup:
  1. 缓存 pip (如果有更新则保存)
  2. 清理 git 配置和 submodule
  3. 清理孤儿进程

警告: Node.js 20 actions deprecated
       → 2026-06-02 起默认使用 Node.js 24
```

---

## 日志中的特殊标记

| 标记 | 含义 | 示例 |
|---|---|---|
| `##[group]...##[endgroup]` | 折叠组, GitHub UI 中可折叠 | 每个步骤的开始/结束 |
| `##[error]` | 错误, 导致 job 失败 | `Process completed with exit code 1.` |
| `##[warning]` | 警告, 不阻断 job | Node.js 20 deprecation |
| `^[[36;1m...^[[0m` | ANSI 颜色转义 (shell 高亮命令) | 实际的命令行执行 |
| `###[debug]` | 调试信息 | 仅启用 Step Debug 时显示 |

---

## CI 时间消耗分布

```
Set up job:          <1s
Checkout code:       <1s
Setup Python:        <1s  (缓存命中 66MB)
Install deps:       ~15s  (79 packages, pip 缓存)
Ruff check:         <1s
Ruff format check:  <1s
Test:               ~6s  (15 tests, SQLite)
Post cleanup:       <1s
─────────────────────────
总计:               ~28s
```

---

## 失败日志示例 (对比)

> 以下是从早期失败运行中摘录的日志结构:

### email-validator 错误

```
ImportError while loading conftest '.../conftest.py'
E   ImportError: email-validator is not installed
    → pip install 'pydantic[email]'
##[error]Process completed with exit code 4.
```

**exit code 含义**:
- `1`: 一般错误 (ruff 发现代码问题)
- `4`: pytest 内部错误 (导入失败, 依赖缺失)

### aiosqlite 错误

```
ModuleNotFoundError: No module named 'aiosqlite'
##[error]Process completed with exit code 4.
```

### Ruff 语法错误

```
18 |     except JWTError:
   |     ^^^^^^^^^^^^^^^^ B904
##[error]Process completed with exit code 1.
```

---

## 关键文件路径 (CI 运行中)

| 路径 | 用途 |
|---|---|
| `/home/runner/work/livehappy/livehappy` | 仓库根目录 |
| `/home/runner/work/livehappy/livehappy/backend` | 后端代码 |
| `/opt/hostedtoolcache/Python/3.12.13/x64` | Python 解释器 |
| `/home/runner/.cache/pip` | pip 缓存 |
| `/home/runner/work/_temp/` | 临时文件 |
