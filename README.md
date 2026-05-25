# 折线统计图 — 学习单

小学数学"折线统计图"在线答题系统。学生通过选择题、填空题、自我检查完成学习单，教师可查看全班答题情况与正确率。

## 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | Vue 3 + Pinia + Vue Router + Axios + Vite |
| 后端 | Python Flask + SQLite |
| 部署 | Docker 多阶段构建 |

## 学生答题流程

```
登录 → 数据预览 → Q1-Q7 选择题 → Q8 填空题 → 自我检查 → 提交成功
```

- **Q1-Q6**：折线统计图基础概念选择题
- **Q7**：汽车行程图像选择题（4 张 SVG 折线图选项，2×2 网格）
- **Q8**：水加热实验填空题（含水温变化 SVG 折线图，4 个空）
- **自我检查**：学生自评学习效果后提交

## 教师看板

访问 `/teacher`，默认账号 `admin` / `password`。

- **Dashboard**：查看全班提交状态、各题正确率、Q8 填空题正确数
- **StudentDetail**：查看单个学生的详细答案与对错

## 本地开发

```bash
# 后端
cd backend
pip install -r requirements.txt
python app.py          # 启动在 :5001

# 前端（新终端）
cd frontend
npm install
npm run dev            # 启动在 :5173，API 代理到 :5001
```

## Docker 部署

```bash
docker build -t line-chart-app .
docker run -p 5001:5001 line-chart-app
```

访问 `http://localhost:5001`。

## 项目结构

```
├── backend/
│   ├── app.py           # Flask 主应用、SPA fallback
│   ├── models.py        # SQLite 表结构、参考答案
│   ├── auth.py          # 学生/教师登录
│   ├── submit.py        # 提交与自动批改
│   ├── teacher.py       # 教师端 API
│   ├── requirements.txt
│   └── static/          # 前端构建产物（gitignore）
├── frontend/
│   └── src/
│       ├── router/      # 路由配置
│       ├── stores/      # Pinia 状态管理
│       ├── views-student/  # 学生端页面
│       ├── views-teacher/  # 教师端页面
│       ├── api.js       # Axios API 封装
│       └── style.css    # 全局样式
├── Dockerfile
└── README.md
```
