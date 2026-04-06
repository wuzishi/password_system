# 团队协作密码管理平台

企业级团队密码管理系统，支持多类型凭据管理、SSH 终端、SFTP 文件管理、审批工作流和动态权限控制。

## 功能概览

### 密码管理
- **多类型支持** — 网站密码、服务器密码、数据库密码、API 密钥、其他
- **AES-256-GCM 加密** — 所有密码 AES-256-GCM 加密存储，Fernet 兼容迁移
- **二次验证** — 查看密码需输入登录密码，5 分钟解密会话
- **密码生成器** — 可配置长度和字符集，强度可视化

### 服务器管理
- **Web SSH 终端** — 基于 xterm.js 的网页终端，支持全屏操作
- **SFTP 文件管理** — 分屏布局：左侧文件浏览器 + 右侧终端，支持上传/下载/删除/重命名
- **终端联动** — 终端 `cd` 切换目录后文件管理器自动同步（procfs 轮询）
- **远程改密** — 一键修改服务器密码，实时展示命令执行过程，原子性操作（验证→修改→确认→入库）
- **连接验证** — SSH 连接测试，自动定时验证，90 天过期提醒

### 数据库管理
- **在线改密** — 支持 MySQL/PostgreSQL 远程修改密码，终端风格实时展示 SQL 执行过程
- **连接验证** — 数据库连接测试

### 安全体系
- **4 级安全等级** — 个人 / 高 / 中 / 低，不同等级不同访问控制
- **动态 RBAC** — 管理员可视化配置角色权限矩阵（页面级 + 功能级）
- **审批工作流** — 未授权用户申请权限，管理员审批后自动授权
- **JWT 双 Token** — 30 分钟 access token + 7 天 refresh token，jti 黑名单支持登出
- **频率限制** — 登录/解密/验证接口限流，防暴力破解
- **安全头** — CSP / HSTS / X-Frame-Options / Referrer-Policy 全套
- **审计日志** — 所有敏感操作（查看/修改/删除/分享）完整记录

### 团队协作
- **邮件邀请** — 管理员邮件邀请用户注册，支持角色预设
- **团队管理** — 创建团队，按团队维度管理密码
- **权限授权** — 管理员可对单个密码给单个用户授权（只读/读写）
- **全局可见** — 所有用户可见所有条目（个人密码除外），操作需授权

### 界面
- **深色/浅色主题** — 一键切换，CSS 变量驱动
- **中文界面** — 全中文操作界面
- **响应式布局** — 侧边栏可折叠，内容区全宽

## 技术架构

```
前端                          后端                         数据库
Vue 3 + Vite            FastAPI + SQLAlchemy          MySQL 8.0
Element Plus            Paramiko (SSH/SFTP)           utf8mb4
Pinia                   AES-256-GCM / Fernet
xterm.js                JWT + bcrypt
Axios                   slowapi (限流)
```

## 项目结构

```
password_system/
├── backend/
│   ├── app/
│   │   ├── api/              # API 路由
│   │   │   ├── auth.py       # 登录/注册/刷新token
│   │   │   ├── passwords.py  # 密码 CRUD + 解密 + 验证
│   │   │   ├── ws.py         # WebSocket (SSH终端/改密)
│   │   │   ├── sftp.py       # SFTP 文件操作
│   │   │   ├── approvals.py  # 审批工作流
│   │   │   ├── permissions.py# 权限管理
│   │   │   ├── users.py      # 用户/邀请管理
│   │   │   ├── teams.py      # 团队管理
│   │   │   └── audit.py      # 审计日志
│   │   ├── models/           # SQLAlchemy 模型
│   │   ├── schemas/          # Pydantic 校验
│   │   ├── services/         # 业务服务 (加密/认证/调度)
│   │   ├── middleware/       # 安全头中间件
│   │   └── core/             # 角色/权限定义
│   ├── .env.example          # 环境变量模板
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── views/            # 页面组件 (13个)
│   │   ├── components/       # 通用组件
│   │   │   ├── WebTerminal.vue    # SSH 终端
│   │   │   ├── FileManager.vue    # SFTP 文件管理器
│   │   │   ├── SplitPane.vue      # 分屏容器
│   │   │   └── layout/AppLayout.vue
│   │   ├── stores/           # Pinia 状态管理
│   │   ├── api/              # API 客户端
│   │   └── router/           # 路由 + 权限守卫
│   ├── nginx.conf
│   └── Dockerfile
├── security_tests/
│   └── pentest.py            # 自动化渗透测试 (45项)
├── docker-compose.yml
└── README.md
```

## 快速开始

### 环境要求

- Python 3.12+
- Node.js 20+
- MySQL 5.7+ / 8.0

### 本地开发

```bash
# 1. 克隆项目
git clone https://github.com/wuzishi/password_system.git
cd password_system

# 2. 后端
cd backend
cp .env.example .env
# 编辑 .env 填入数据库连接和密钥（参考 .env.example 中的生成命令）
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000

# 3. 前端
cd ../frontend
npm install
npx vite --port 3000 --host 0.0.0.0

# 4. 访问 http://localhost:3000
# 首次启动会创建管理员账号，密码打印在后端控制台
```

### Docker 部署

```bash
# 1. 配置环境变量
cd backend
cp .env.example .env
# 编辑 .env 填入必要配置

# 2. 启动
cd ..
export DB_ROOT_PASSWORD=your_secure_password
docker-compose up -d

# 3. 访问 http://localhost:3000
```

## 环境变量

| 变量 | 说明 | 必填 |
|------|------|------|
| `DATABASE_URL` | MySQL 连接字符串 | 是 |
| `JWT_SECRET` | JWT 签名密钥 | 是 |
| `AES_KEY` | AES-256 加密密钥 (base64) | 是 |
| `FERNET_KEY` | Fernet 加密密钥 | 是 |
| `ADMIN_PASSWORD` | 初始管理员密码（留空自动生成） | 否 |
| `CORS_ORIGINS` | 允许的前端地址（逗号分隔） | 否 |
| `SMTP_HOST` | 邮件服务器 | 否 |
| `SITE_URL` | 前端地址（邀请邮件中使用） | 否 |

密钥生成命令见 `backend/.env.example`。

## 安全测试

```bash
cd security_tests
python pentest.py --base-url http://localhost:8000 --admin-user admin --admin-pass 'your_password'
```

覆盖 12 类测试项（45 个测试点）：SQL 注入、XSS、认证绕过、越权访问、安全头、信息泄露、频率限制、路径穿越、JWT 安全、业务逻辑、HTTP 方法、密码策略。

## 角色权限

| 功能 | 管理员 | 产品 | 开发 |
|------|--------|------|------|
| 密码库 | 全部操作 | 查看/创建 | 查看/创建 |
| 服务器终端 | 可用 | 按配置 | 可用 |
| 远程改密 | 可用 | 按配置 | 可用 |
| 团队管理 | 可用 | - | - |
| 用户管理 | 可用 | - | - |
| 审批管理 | 审批 | 申请 | 申请 |
| 权限管理 | 可用 | - | - |
| 审计日志 | 可用 | - | - |

权限矩阵可由管理员在「权限管理」页面动态调整。

## License

MIT
