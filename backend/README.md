# YanCare 后端服务

养发馆管理系统后端 API，基于 FastAPI 构建。

## 技术栈

- **框架**: FastAPI
- **数据库**: SQLite (开发) / MySQL (生产)
- **ORM**: SQLAlchemy 2.0 (异步)
- **认证**: JWT
- **AI**: DeepSeek API

## 快速开始

### 1. 安装依赖

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 文件，填写配置
```

### 3. 初始化数据库

```bash
python -m scripts.init_data
```

### 4. 启动服务

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 5. 查看 API 文档

访问 http://localhost:8000/docs

## API 接口

### 认证
- `POST /api/auth/wechat-login` - 微信登录
- `GET /api/auth/me` - 获取当前用户信息

### 门店
- `GET /api/stores` - 获取门店列表（支持距离排序）
- `GET /api/stores/{id}` - 获取门店详情
- `POST /api/stores` - 创建门店（管理员）

### 卡管理
- `GET /api/cards/types` - 获取卡类型列表
- `GET /api/cards/my-cards` - 获取我的卡（客户端）
- `POST /api/cards/add-card` - 给用户开卡（员工端）

### 排班
- `GET /api/schedules/available-staff` - 获取可预约员工
- `POST /api/schedules` - 创建排班（员工端）
- `POST /api/schedules/batch` - 批量创建排班

### 预约
- `POST /api/appointments` - 创建预约（客户端）
- `GET /api/appointments/my-appointments` - 我的预约
- `POST /api/appointments/{id}/complete` - 核销预约（员工端）
- `GET /api/appointments/staff-stats` - 业绩统计

### AI 咨询
- `POST /api/ai/chat` - AI 对话
- `GET /api/ai/suggestions` - 推荐问题

## 项目结构

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py          # FastAPI 入口
│   ├── config.py        # 配置
│   ├── database.py      # 数据库连接
│   ├── models/          # 数据库模型
│   ├── schemas/         # Pydantic 模型
│   ├── routers/         # API 路由
│   └── services/        # 业务逻辑
├── scripts/
│   └── init_data.py     # 初始化数据脚本
├── requirements.txt
├── .env.example
└── README.md
```

## 部署

### 生产环境配置

1. 修改 `.env`:
```
DEBUG=false
SECRET_KEY=<生成一个强密码>
DATABASE_URL=mysql+aiomysql://user:pass@host/yancare
```

2. 使用 gunicorn 启动:
```bash
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000
```

### Docker 部署

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```
