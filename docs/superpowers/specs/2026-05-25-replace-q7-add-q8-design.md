# 替换 Q7 + 新增 Q8 填空题 — 设计文档

## 概述

将现有选择题第 7 题（预测题）替换为"汽车行程图像选择题"，并在选择题页与绘图题之间插入一道新的 Q8 填空题（"水加热实验"）。

## 页面流程（更新后）

```
登录页 → 统计表阅读页 → 选择题页(Q1-Q7) → 填空题页(Q8) → 绘图题 → 自我检查 → 提交成功
```

## 数据模型变更

### answers 表

```sql
-- CHECK 约束扩展
-- 旧: CHECK(question_no BETWEEN 1 AND 7)
-- 新: CHECK(question_no BETWEEN 1 AND 8)

-- 新增子题号字段
ALTER TABLE answers ADD COLUMN sub_no INTEGER NOT NULL DEFAULT 0;
```

- `sub_no = 0`：普通选择题（Q1-Q7）
- `sub_no = 1~4`：Q8 的4个子空

唯一约束调整为 `UNIQUE(student_id, question_no, sub_no)`。

`init_db()` 中同步更新表定义。

## 参考答案

```python
# 选择题（Q7 更新为 D）
REFERENCE_ANSWERS = {1: 'A', 2: 'B', 3: 'A', 4: 'B', 5: 'A', 6: 'A', 7: 'D'}

# 填空题（Q8 含4个子空，答案不区分大小写，trim 后比对）
FILL_BLANK_ANSWERS = {8: {1: '25', 2: '4', 3: '11', 4: '100'}}
```

## 后端变更

### submit.py

提交 payload 新增 `fill_blank` 字段：

```json
{
  "student_id": 1,
  "answers": [{ "question_no": 1, "answer": "A" }, ...],
  "fill_blank": { "8": { "1": "25", "2": "4", "3": "11", "4": "100" } },
  "drawing_points": [[...], ...],
  "self_check": { ... }
}
```

Q8 的4个子空逐条写入 answers 表（question_no=8, sub_no=1~4, answer=学生输入），后端逐一比对 `FILL_BLANK_ANSWERS` 评分，结果合并到 `scores` 返回。

### teacher.py

- Dashboard：统计时计入 Q8（可暂时按"是否作答"展示状态）
- StudentDetail：展示 Q8 的4个子空答案及对错

## 前端变更

### ChoiceQuestions.vue

- Q7 题目文字和选项替换为"汽车行程"内容
- "进入绘图题"按钮文字改为"进入填空题"，路由跳转目标改为 `/fill-blank`

### 新增 FillBlankQuestion.vue

卡片式布局：
- 顶部：参考数据区（水加热实验统计表：时间 0-11 分对应水温 25-100℃）
- 中部：题干文字 + 4个填空题输入框
- 底部：上一题 / 进入绘图题 导航按钮

4个填空：
1. 加热前水温是 ____ ℃
2. 水加热到 60℃ 时，用了 ____ 分钟
3. 烧开这壶水一共用了 ____ 分钟
4. 如果持续加热到第 16 分钟，此时水温是 ____ ℃

### Store（student.js）

新增 `fillBlank` 响应式对象和 setter/reset：

```js
const fillBlank = ref({ 8: { 1: '', 2: '', 3: '', 4: '' } })
```

### Router（index.js）

在 `/questions` 和 `/drawing` 之间插入 `/fill-blank` 路由。

### SubmitSuccess / DataPreview

流程衔接：SubmitSuccess 的"切换用户"按钮已返回登录页，无需改动；DataPreview 的"开始答题"进入 Q1，无需改动。

## 教师端变更

- Dashboard：表格新增 Q7、Q8 列
- StudentDetail：展示 Q7 选项、Q8 的4个子空答案及对错
- 绘图回放区域不变

## 迁移说明

现有数据库中的 answers 数据（旧 Q7 预测题"能否预测许明哲周日的仰卧起坐成绩"）保持不变，`sub_no = 0`。新提交将使用新 Q7（D）和新 Q8（4个子空）。教师端查看旧数据时 Q7 答案仍可显示原始值。
