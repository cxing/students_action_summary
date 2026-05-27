# 折线统计图学习单 — 闯关游戏重设计

## 概述

将现有 8 道题目（Q1-Q7 选择 + Q8 填空）全部替换为 5 道闯关游戏题（关卡制），面向小学五年级学生。每题即时提交，不做对也能进下一关。教师端新增一键生成柱状图功能。

## 学生流程

```
登录 → 关卡1 → 关卡2 → 关卡3 → 关卡4 → 关卡5 → 提交成功
```

去掉原 `/preview`（数据预览）、`/self-check`（自我检查）。

## 5 关游戏设计

| 关卡 | 题型 | 游戏形式 | 知识要点 |
|------|------|----------|---------|
| 🔫 第1关 | 选择 | 飞镖射气球配对"点""线"含义 | 点=数量多少，线=变化趋势 |
| 🧩 第2关 | 拖拽 | 两张场景卡片拖入"条形图"/"折线图"篮子 | 比较用条形图，变化用折线图 |
| 🚗 第3关 | 选择 | 看小车行驶动画，从 4 张折线图中选正确图像 | 折线升降平与实际场景对应 |
| 🧪 第4关 | 选择 | 铁棒入水动画（溢出后取出），选正确水位折线图 | 折线反映物理变化过程 |
| 🌡️ 第5关 | 填空 | 读水温折线图填 4 个空，温度计动画反馈 | 从折线图读取具体数值 |

### 星级规则

- 第 1 次答对 → ⭐⭐⭐
- 第 2 次答对 → ⭐⭐
- 第 3 次及以上 → ⭐
- 未答/跳过 → 0 ⭐
- 共 5 关，满分 15 ⭐

### 关卡解锁

进入时全部可访问，不做对也能进下一关。星级仅用于鼓励，不阻塞进度。

## 题目具体内容

### 第1关：点与线的含义
题目："折线统计图中的'点'和'线'分别表示什么？"
选项：
- A. 数量的多少；数量的变化趋势（正确答案）
- B. 图形的颜色；数量的单位
- C. 统计图的标题；横轴的长度

### 第2关：条形图 vs 折线图
统计表一：6名同学一分钟仰卧起坐个数 → 用条形统计图（A）
统计表二：许明哲连续6天成绩 → 用折线统计图（B）
两个子题，分别拖拽分类。

### 第3关：汽车行程（原 Q7）
小明一家驾车去湿地公园，50km/h 行驶 1 小时，公园玩 3 小时，原速返回。
4 张 SVG 折线图选项（A/B/C/D），正确为 D（离家距离，上升-水平-下降至 0）。

### 第4关：铁棒入水
容器中有水，圆柱铁棒垂直匀速放入 → 溢出 800ml → 匀速取出。
核心逻辑：水溢出后不再回来，因此取出后水位低于原水位。
4 张"深度-时间"折线图，正确为 A（终点低于虚线原水位）。

### 第5关：水温加热（原 Q8）
展示水温变化折线图（0-12 分钟，25℃→100℃），填 4 个空：
- 加热前水温 25℃
- 到 60℃ 用了 4 分钟
- 烧开一共用了 11 分钟
- 第 16 分钟水温 100℃

## 技术架构

### 路由

| 路由 | 组件 | 说明 |
|------|------|------|
| `/` | StudentLogin.vue | 学生登录（保留） |
| `/level/1` | Level1Balloon.vue | 射击气球 |
| `/level/2` | Level2DragDrop.vue | 拖拽分类 |
| `/level/3` | Level3CarRide.vue | 汽车动画 |
| `/level/4` | Level4WaterTank.vue | 水位实验 |
| `/level/5` | Level5Thermometer.vue | 温度填空 |
| `/submit-success` | SubmitSuccess.vue | 提交成功（保留） |
| `/teacher` | TeacherLogin.vue | 教师登录（保留） |
| `/teacher/dashboard` | Dashboard.vue | 仪表盘（改） |
| `/teacher/student/:id` | StudentDetail.vue | 学生详情（改） |

删除路由：`/preview`、`/questions`、`/fill-blank`
删除组件：DataPreview.vue、ChoiceQuestions.vue、FillBlankQuestion.vue、DrawingQuestion.vue、SelfCheck.vue

### Pinia Store

```javascript
// 新增
levels: {
  1: { answer: null, stars: 0, attempts: 0 },
  2: { answer: null, stars: 0, attempts: 0 },
  3: { answer: null, stars: 0, attempts: 0 },
  4: { answer: null, stars: 0, attempts: 0 },
  5: { answer: null, stars: 0, attempts: 0 },
}

// 废弃
answers, fillBlank, drawingPoints, selfCheck
```

### 数据库

```sql
-- 改动 answers 表：CHECK question_no 从 1-8 改为 1-5
-- 新增 level_stars 表
CREATE TABLE level_stars (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL,
    level_no INTEGER NOT NULL CHECK(level_no BETWEEN 1 AND 5),
    stars INTEGER NOT NULL DEFAULT 0 CHECK(stars BETWEEN 0 AND 3),
    attempts INTEGER NOT NULL DEFAULT 0,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES students(id),
    UNIQUE(student_id, level_no)
);
-- 删除 drawings 表、self_check 表
```

### 参考答案

```python
REFERENCE_ANSWERS = {
    1: 'A',
    2: {'table1': 'A', 'table2': 'B'},
    3: 'D',
    4: 'A',
}
FILL_BLANK_ANSWERS = {
    5: {1: '25', 2: '4', 3: '11', 4: '100'},
}
```

### 后端 API

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/level/submit` | 单关即时提交（含 answer + stars + attempts） |
| GET | `/api/teacher/dashboard` | 改为返回 5 题数据 + stars |
| GET | `/api/teacher/student/<id>` | 改为返回 5 题答案 + stars |
| DELETE | `/api/teacher/student/<id>` | 改为同时删除 level_stars |
| GET | `/api/teacher/chart?type=questions\|stars` | 新增：返回柱状图 PNG |

### 教师端柱状图

后端 matplotlib 生成 PNG，前端预览 + 下载。

- `type=questions`：X 轴 Q1-Q5，Y 轴正确人数，柱顶标数字
- `type=stars`：X 轴 0-3 / 4-6 / 7-9 / 10-12 / 13-15 区间，Y 轴人数

### 前端改动要点

- 每题/每关游戏效果用 CSS animation + SVG 实现，不引入外部动画库
- 拖拽（第2关）使用原生 HTML5 Drag and Drop API
- 动画（第3、4关）使用 CSS keyframes 控制 SVG 元素运动
- 教师端柱状图预览用 `<img>` 加载后端 PNG，下载用 `<a download>`
