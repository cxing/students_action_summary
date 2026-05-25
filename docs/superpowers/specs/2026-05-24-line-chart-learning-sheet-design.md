# 折线统计图学习单 — 前后端系统设计

## 概述

Vue 3 + Flask REST API + SQLite 的前后端分离 Web 应用。学生在浏览器中完成折线统计图学习单（7道选择题 + 1道绘图题 + 自我检查），教师在教师端查看全班答题概览和每位学生的详细作答。

## 技术栈

- **前端**: Vue 3 (Composition API) + Vue Router + Axios + Canvas API（绘图题）
- **后端**: Flask + SQLite（单文件数据库）
- **构建**: Vite（开发代理到 Flask，生产静态文件由 Flask 直出）

## 认证

- **学生登录**: 仅输入姓名，后端按姓名查 students 表（有则复用，无则新建）
- **教师登录**: 硬编码 `admin / password`，Flask session 校验
- **学生隔离**: 前端传入 student_id，后端不做认证拦截，同名学生共享记录

## 数据模型

### students
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PK | 自增 |
| name | TEXT NOT NULL | 学生姓名 |
| created_at | TIMESTAMP | 首次登录时间 |

### answers
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PK | 自增 |
| student_id | INTEGER FK | 关联 students.id |
| question_no | INTEGER | 题号 1-7 |
| answer | TEXT | 学生选项 A/B/C |
| is_correct | INTEGER | 0/1，后端自动比对参考答案 |
| updated_at | TIMESTAMP | 最后更新时间 |

**UNIQUE(student_id, question_no)** 约束，提交时 upsert。

### drawings
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PK | 自增 |
| student_id | INTEGER FK | 关联 students.id |
| points | TEXT (JSON) | 6个坐标 `[[x1,y1],...,[x6,y6]]` |
| auto_score | TEXT (JSON) | `{"points_correct": true, "labels_complete": true, "in_order": true, "trend": "上升"}` |
| created_at | TIMESTAMP | 提交时间 |

### self_check
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PK | 自增 |
| student_id | INTEGER FK | 关联 students.id |
| point_check | TEXT | "能" / "还不确定" |
| line_check | TEXT | "能" / "还不确定" |
| draw_check | TEXT | "能" / "还不确定" |
| note | TEXT | 还需注意的事项 |
| created_at | TIMESTAMP | 提交时间 |

## 参考答案（后端硬编码）

| 题号 | 答案 |
|------|------|
| 1 | A |
| 2 | B |
| 3 | A |
| 4 | B |
| 5 | A |
| 6 | A |
| 7 | A |

绘图题评分：6个点容差 ±2，与标准坐标比较。

## REST API

### POST /api/student/login
```
请求: { "name": "周子昂" }
响应: { "student_id": 1, "name": "周子昂" }
```

### POST /api/teacher/login
```
请求: { "username": "admin", "password": "password" }
响应: { "ok": true }
```
使用 Flask session 保持登录态。

### POST /api/submit（统一提交）
```
请求: {
  "student_id": 1,
  "answers": [{ "question_no": 1, "answer": "A" }, ...],
  "drawing_points": [[x1,y1], ..., [x6,y6]],
  "self_check": { "point_check": "能", "line_check": "能", "draw_check": "还不确定", "note": "..." }
}
响应: {
  "ok": true,
  "scores": { "1": true, "2": true, ... },
  "drawing_score": { "points_correct": true, "labels_complete": true, "in_order": true, "trend": "上升" }
}
```
后端逐题比对参考答案，写入 answers 表；绘图坐标比对标准值，写入 drawings 表；self_check 写入 self_check 表。所有操作在一个事务中完成。

### GET /api/teacher/dashboard
```
响应: {
  "students": [{ "id": 1, "name": "周子昂", "answers": {...}, "scores": {...}, "drawing_submitted": true }, ...],
  "stats": { "submitted": 3, "total": 6 }
}
```

### GET /api/teacher/student/<id>
```
响应: { "id": 1, "name": "周子昂", "answers": [...], "drawing": {...}, "self_check": {...} }
```

## 学生端页面流程

1. **登录页** — 输入姓名，POST /api/student/login，获取 student_id 存入 Vue store
2. **统计表阅读页** — 展示统计表一和统计表二，学生阅读后点击"开始答题"
3. **选择题页（1-7）** — 逐题呈现，点击选项选中，支持前后翻页。Q7 为预测题（A.45 B.50 C.20）
4. **绘图题** — Canvas 方格图，横轴周一至周六，纵轴 0-45。按顺序点击描点，系统自动标数连线
5. **自我检查页** — 3 个复选框 + 1 个文本补充说明
6. **提交成功页** — 确认提交，显示"切换用户"按钮，点击返回登录页

## 绘图题交互细节

- 横轴: 6 个刻度（周一至周六）
- 纵轴: 0-45，每格 5 单位
- 点击描点: 自动吸附最近网格交叉点，按顺序（周一→周六）
- 描点后: 自动标出数值，6 个点全部描完后自动按序连线
- 重新描点: 清空所有点和线
- 标准坐标（通过 Canvas 坐标转换为数值后验证）:
  - 周一: 30, 周二: 32, 周三: 35, 周四: 36, 周五: 39, 周六: 42
- 自动评分容差: 每个点 ±2

## 教师端页面

1. **登录页** — admin/password
2. **全班概览看板** — 表格：行=学生，列=Q1-7 对错 + 绘图状态 + 详情按钮。顶部统计卡片（提交率、正确率）
3. **学生答题详情** — 逐题答案对比、绘图 SVG 回放、自我检查展示。返回概览按钮

## 平板共用

学生提交后将跳转至"提交成功"页，显示"切换用户"按钮，点击返回登录页，下一个学生输入自己的姓名登录。学生信息通过 student_id 隔离，互不干扰。

## 项目结构

```
students_action_summary/
├── backend/
│   ├── app.py              # Flask 入口，路由注册
│   ├── models.py           # 数据模型 + DB 初始化
│   └── requirements.txt    # Flask
├── frontend/
│   ├── src/
│   │   ├── views/
│   │   │   ├── StudentLogin.vue
│   │   │   ├── DataPreview.vue       # 统计表阅读
│   │   │   ├── ChoiceQuestions.vue   # Q1-7 选择题
│   │   │   ├── DrawingQuestion.vue   # 绘图题 Canvas
│   │   │   ├── SelfCheck.vue
│   │   │   └── SubmitSuccess.vue
│   │   ├── views-teacher/
│   │   │   ├── TeacherLogin.vue
│   │   │   ├── Dashboard.vue
│   │   │   └── StudentDetail.vue
│   │   ├── router/
│   │   │   ├── index.js
│   │   │   ├── student.js
│   │   │   └── teacher.js
│   │   ├── stores/          # Pinia stores
│   │   ├── api.js           # Axios 封装
│   │   ├── App.vue
│   │   └── main.js
│   ├── index.html
│   ├── vite.config.js
│   └── package.json
└── data/
    └── learning.db          # SQLite 数据库文件（gitignore）
```
