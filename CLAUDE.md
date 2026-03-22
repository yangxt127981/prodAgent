# 商品购买咨询 Agent

## 项目概述
基于 Claude API 的家居商品购买咨询 Agent，通过引导式多轮对话帮助用户挑选合适的商品。

## 技术栈
- **后端**: Python 3.9 + FastAPI + Anthropic Claude API
- **前端**: Vue 3 + Vite + marked (Markdown 渲染)
- **数据源**: Excel 产品知识库，解析后存为 JSON

## 项目结构
```
prodAgent/
├── backend/
│   ├── .env                    # 环境变量 (ANTHROPIC_API_KEY)
│   ├── requirements.txt
│   └── app/
│       ├── main.py             # FastAPI 入口，API 路由
│       ├── agent.py            # Claude 对话引擎，系统提示词，多轮对话管理
│       ├── parse_excel.py      # Excel 知识库解析脚本
│       └── knowledge_base.json # 已解析的结构化知识库
└── frontend/
    ├── package.json
    └── src/
        ├── App.vue             # 应用入口
        └── components/
            └── ChatWindow.vue  # 聊天界面组件
```

## 知识库品类
床垫、智能马桶、花洒套装、智能门锁、吸顶灯、台灯、落地护眼灯（共 7 品类，42 款产品，63 个概念解释）

## 启动命令

### 后端
```bash
cd backend
pip3 install -r requirements.txt
python3 -m uvicorn app.main:app --reload --port 8000
```

### 前端
```bash
cd frontend
npm install
npm run dev
```

前端访问地址: http://localhost:5173
后端 API 地址: http://localhost:8000

## API 接口
- `GET  /api/categories` - 获取支持的品类列表
- `POST /api/chat` - 发送消息 `{session_id?, message}` → `{session_id, reply}`
- `POST /api/reset` - 重置对话 `{session_id}`
- `GET  /api/health` - 健康检查

## 更新知识库
当 Excel 文件有更新时，运行以下命令重新生成 JSON：
```bash
cd backend
python3 app/parse_excel.py /path/to/新的Excel文件.xlsx
```

## 功能亮点
- **智能引导提问**：根据品类自动逐步提问（预算、使用人群、需求偏好等），每次只问 1-2 个问题，不会一次性轰炸用户
- **精准产品推荐**：基于 42 款产品的完整知识库，结合用户回答筛选最匹配的 1-3 款产品，并说明推荐理由
- **概念解释**：当涉及专业术语时（如独袋弹簧、恒温阀芯、泡沫盾），自动用通俗语言解释
- **多轮对话记忆**：支持上下文记忆，用户可以追问、修改需求、对比产品
- **快捷品类入口**：首页直接点击品类标签快速开始咨询，降低使用门槛
- **Markdown 渲染**：Agent 回复支持富文本格式，产品推荐以结构化卡片形式展示

## 注意事项
- Python 3.9 环境，代码中使用 `from __future__ import annotations` 兼容类型注解
- 需要 `httpx[socks]` 依赖（代理环境支持）
- `.env` 文件中需配置 `ANTHROPIC_API_KEY`
- Claude 模型使用 `claude-sonnet-4-20250514`
- 前端开发端口 5173，后端 CORS 已配置允许该端口
