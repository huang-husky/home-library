# HomeLib - AI 家庭图书馆

通过拍照批量识别家庭藏书，并自动补全图书信息、进行中图法分类和书柜空间定位。

## 技术栈

### 后端
- **框架**: FastAPI (Python 3.10+)
- **配置**: Pydantic Settings
- **数据库**: SQLite + SQLAlchemy (async) - Phase 1: 仅配置占位

### 前端
- **框架**: React 18 + TypeScript
- **构建**: Vite
- **样式**: Tailwind CSS
- **数据获取**: TanStack Query

## 项目结构

```
home-library/
├── backend/
│   ├── app/
│   │   ├── api/              # API 路由
│   │   │   └── router.py     # 路由聚合
│   │   ├── core/             # 核心配置
│   │   │   ├── __init__.py
│   │   │   └── config.py     # 应用配置
│   │   ├── db/               # 数据库
│   │   │   ├── __init__.py
│   │   │   └── database.py   # 数据库连接
│   │   ├── models/           # 数据模型 (Phase 2+)
│   │   ├── schemas/          # Pydantic Schema (Phase 2+)
│   │   ├── services/         # 业务逻辑 (Phase 2+)
│   │   └── main.py           # 应用入口
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── api/              # API 客户端
│   │   │   └── index.ts
│   │   ├── components/       # 通用组件
│   │   ├── features/         # 功能模块
│   │   ├── hooks/            # 自定义 Hooks
│   │   ├── pages/            # 页面
│   │   │   └── Home.tsx      # 首页占位
│   │   ├── types/            # TypeScript 类型
│   │   ├── utils/            # 工具函数
│   │   ├── App.tsx           # 应用根组件
│   │   └── main.tsx          # 入口
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   └── .env.example
└── README.md
```

## 快速开始

### 1. 启动后端

```bash
cd backend

# 创建虚拟环境
python -m venv venv

# Windows
venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env

# 启动服务
uvicorn app.main:app --reload
```

后端服务将在 http://localhost:8000 运行

**API 端点**:
- `GET /health` - 健康检查
- `GET /docs` - API 文档 (开发模式)

### 2. 启动前端

```bash
cd frontend

# 安装依赖
npm install

# 配置环境变量
cp .env.example .env

# 启动开发服务器
npm run dev
```

前端将在 http://localhost:5173 运行

前端会自动访问后端的 `/health` 端点并显示连接状态。

## 环境变量

### 后端 (.env)
```
APP_NAME=HomeLib
APP_VERSION=1.0.0
DEBUG=true
DATABASE_URL=sqlite+aiosqlite:///./data/homelib.db
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
```

### 前端 (.env)
```
# API 基础 URL（开发时使用 Vite 代理，通常无需设置）
# VITE_API_URL=http://localhost:8000
```

## 开发阶段

### Phase 1: 工程骨架 ✅
- [x] 前端基础结构 (React + TypeScript + Vite)
- [x] 后端基础结构 (FastAPI)
- [x] /health API
- [x] 基础 CORS 配置
- [x] 环境变量配置
- [x] API Client 基础封装

### Phase 2: 数据模型与基础 CRUD ✅
- [x] 数据库模型定义
- [x] 图书 CRUD
- [x] 书柜管理

### Phase 3: 图书元数据服务 ✅
- [x] Google Books Provider
- [x] Open Library Provider
- [x] 元数据搜索 API

### Phase 4: AI 识别 MVP ✅
- [x] OCR Provider
- [x] 书脊检测
- [x] 批量识别流程

### Phase 5: 自动入库闭环 ✅
- [x] 识别 → 查询 → 匹配 → 确认 → 入库

### Phase 6: 分类与空间定位 ✅
- [x] 中图法分类
- [x] AI 分类推荐
- [x] 空间位置记录

### Phase 7-10: 扫描识别与位置跟踪 ✅
- [x] 书架图片扫描
- [x] AI 图书导入管道
- [x] 中图法分类系统
- [x] 书架位置可视化

## License

MIT
