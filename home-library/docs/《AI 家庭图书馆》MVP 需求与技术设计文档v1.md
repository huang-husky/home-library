# 《AI 家庭图书馆》MVP 需求与技术设计文档

**项目代号：HomeLib**
**版本：V1.0（MVP 定稿）**
**目标：建立一个低录入成本、AI 驱动的个人/家庭数字图书馆。**

## 1. 项目定位

HomeLib 面向拥有数百至数千本实体书的个人或家庭，通过**拍照识别 + 图书元数据检索 + AI 辅助分类 + 人工确认**，低成本完成家庭藏书数字化。

核心价值：

> **不要求用户一本一本录入，而是让用户拍一张书柜照片，系统批量识别并建立图书档案。**

V1 的核心目标不是做完整的阅读社区，而是解决三个问题：

**我有什么书？在哪里？是什么书？**

---

# 2. MVP 核心流程

```text
用户拍摄一层书柜
        ↓
上传图片
        ↓
AI / OCR 识别书脊
        ↓
得到书名候选
        ↓
查询图书元数据
        ↓
AI 匹配具体版本
        ↓
AI 推荐中图法分类
        ↓
用户确认
        ↓
写入个人书库
        ↓
记录书柜 / 层 / 位置
```

V1 必须跑通这一条完整链路。

---

# 3. MVP 功能范围

## 3.1 图书管理

支持：

* 新增图书
* 编辑图书
* 删除图书
* 查看图书详情
* 搜索图书
* 按分类、作者、标签筛选

图书基础信息：

* 书名
* 副标题
* 作者
* ISBN
* 出版社
* 出版日期
* 语言
* 页数
* 封面
* 简介
* 中图法分类
* AI 标签
* 所在书柜
* 所在层
* 空间位置
* 数据来源
* 识别置信度

---

## 3.2 书柜管理

支持：

```text
书柜
 ├── 第1层
 ├── 第2层
 ├── 第3层
 └── 第4层
```

每个书柜记录：

* 名称
* 位置
* 宽度
* 高度
* 描述

每层记录：

* 所属书柜
* 层级
* 高度
* 当前扫描照片

你的约 1 米宽书柜可以直接作为默认测试场景。

---

## 3.3 批量扫描

用户：

> 选择书柜 → 选择层 → 上传/拍摄照片。

系统返回：

```text
发现 32 本书

✅ 高可信：27
⚠️ 待确认：4
❌ 无法识别：1
```

用户可以逐本确认，也可以批量确认。

---

## 3.4 图书信息自动补全

识别到：

> 《置身事内》

系统自动查询图书数据源，获取：

* 作者
* 出版社
* 出版日期
* ISBN
* 封面
* 页数
* 简介

首期采用：

**Google Books + Open Library**

作为可替换的 Metadata Provider。

---

## 3.5 AI 版本匹配

针对同名或不同版本图书：

```text
识别：
《经济学原理》

候选：
A. 机械工业出版社 / 2015
B. 北京大学出版社 / 2012
C. ……
```

AI 根据书名、作者、封面、ISBN 等证据进行匹配。

必须允许：

> **人工修改 AI 的判断。**

---

## 3.6 中图法分类

系统保存：

```text
分类号：TP181
分类名：机器学习……
```

分类流程：

```text
图书信息
 ↓
AI 推荐
 ↓
从合法分类树选择
 ↓
系统验证分类号
 ↓
保存
```

**禁止 AI 自由生成一个未经验证的分类号。**

同时保存：

* 分类号
* 分类名称
* 分类置信度
* 分类理由

---

## 3.7 AI 标签

标准分类之外，系统允许 AI 生成多个易搜索标签。

例如：

```text
TP181

#机器学习
#人工智能
#深度学习
#算法
```

---

## 3.8 空间定位

V1 保存：

```text
书柜 A
第 3 层
position_x = 0.63
```

前端可以显示为：

> 书柜 A / 第 3 层 / 左起约第 17 本

**数据库优先保存相对位置，而不是把“第17本”作为唯一位置依据。**

为未来重新扫描和位置更新保留空间。

---

# 4. AI 识别架构

采用模块化 Pipeline：

```text
图片
 ↓
Image Preprocessing
 ↓
Book Detection
 ↓
OCR / Vision
 ↓
Book Text
 ↓
Metadata Search
 ↓
Edition Matching
 ↓
Classification
 ↓
Confidence
 ↓
Human Confirmation
 ↓
Database
```

AI 不直接决定所有事实。

原则：

> **AI 负责理解和判断，外部数据源负责提供事实，用户负责最终确认。**

---

# 5. 置信度机制

统一采用三级：

### 高可信

`>= 0.90`

自动进入待确认结果，可支持批量确认。

### 中可信

`0.70 ~ 0.90`

要求用户确认。

### 低可信

`< 0.70`

进入人工处理。

所有 AI 结果都必须保留：

```text
confidence
reason
source
```

---

# 6. 数据模型

核心模型确定为：

```text
Work
   ↓
Edition
   ↓
Book
   ↓
ShelfPosition
```

含义：

### Work

“这是什么作品”。

### Edition

“具体哪个出版版本”。

### Book

“我家实际拥有的这一册”。

### ShelfPosition

“这一册现在放在哪里”。

---

## 核心表

```text
works
editions
books
authors
categories
tags
book_tags
bookshelves
shelves
shelf_positions
scans
scan_items
metadata_sources
```

V1 可以适当简化，但以上逻辑必须保留。

---

# 7. 推荐技术栈

## 前端

**React + TypeScript + Vite**

## 后端

**FastAPI + Python**

## 数据库

**SQLite**

## ORM

**SQLAlchemy**

## 图像处理

**OpenCV + Pillow**

## OCR

设计为：

```text
OCRProvider
```

可以接：

* PaddleOCR
* 云 OCR
* Vision Model

## AI

设计为：

```text
LLMProvider
VisionProvider
```

不绑定单一模型厂商。

## 图书信息

设计为：

```text
MetadataProvider
```

首期：

* Google Books
* Open Library

## 部署

**本地优先**

第一阶段不考虑复杂云架构。

---

# 8. 项目结构

```text
home-library/
│
├── frontend/
│   └── src/
│       ├── pages/
│       ├── components/
│       ├── features/
│       ├── api/
│       └── types/
│
├── backend/
│   └── app/
│       ├── api/
│       ├── models/
│       ├── schemas/
│       ├── services/
│       │   ├── ai/
│       │   ├── ocr/
│       │   ├── books/
│       │   ├── classification/
│       │   └── recognition/
│       └── main.py
│
├── data/
│   ├── classification/
│   └── seeds/
│
├── storage/
│   ├── scans/
│   ├── covers/
│   └── thumbnails/
│
└── docs/
```

---

# 9. 页面设计

MVP 只做 5 个核心页面。

### 首页

展示：

* 总藏书量
* 已分类
* 待确认
* 最近添加
* 搜索
* 扫描书柜
* 添加图书

### 图书馆

支持：

* 卡片/列表
* 搜索
* 筛选
* 排序

### 扫描页面

```text
选择书柜
→ 选择层
→ 上传照片
→ AI 识别
→ 确认
```

### 待确认页面

集中处理：

* 版本冲突
* 识别错误
* 分类确认
* 无法识别的图书

### 图书详情

展示：

* 封面
* 书名
* 作者
* ISBN
* 出版信息
* 分类
* 标签
* 位置
* 来源
* AI 识别信息

---

# 10. MVP 暂不实现

以下功能全部进入后续版本：

* 借阅管理
* 多用户权限
* 社交
* 读书社区
* 阅读统计
* AI 长文本总结
* 书籍知识图谱
* 自动重新扫描整个家庭书库
* 自然语言推荐
* 复杂移动端原生 App

---

# 11. MVP 验收标准

MVP 不是“页面能跑”，而是必须证明 AI 能够减少录入工作。

建立一个真实测试集：

> **20～50 本书**

包含：

* 中文书
* 英文书
* 不同厚度
* 窄书脊
* 同名不同版本
* 带副标题
* 不同字体/颜色
* 随机排列

记录：

```text
Book Detection Recall
OCR Accuracy
Metadata Match Accuracy
Classification Accuracy
Human Correction Rate
```

最重要的指标：

> **人工处理 100 本书所需时间**

目标是相较于逐本录入显著降低人工成本。

---

# 12. 开发顺序

严格按照以下顺序，不跳。

### Phase 1

**数据库 + 基础图书管理**

先实现：

> Book / Bookshelf / Shelf / Category CRUD + 搜索

### Phase 2

**Metadata Provider**

实现：

> ISBN / 标题 → 图书信息

### Phase 3

**AI 识别 MVP**

实现：

> 一张书架照片 → 书籍候选列表

### Phase 4

**自动建库闭环**

实现：

> 图片 → 识别 → 查询 → 匹配 → 确认 → 入库

### Phase 5

**中图法分类**

实现：

> 分类树 + AI 推荐 + 合法性校验

### Phase 6

**空间定位**

实现：

> 书柜 → 层 → 相对空间位置

### Phase 7

**体验优化**

实现：

> AI 搜索、重新扫描、智能推荐等。

---

# 13. 第一阶段具体任务

现在不要同时开发所有模块。

### 当前 Sprint 1：

**只完成以下 5 件事：**

```text
1. 创建 GitHub 项目
2. 初始化 frontend / backend
3. 建立 SQLite + SQLAlchemy
4. 建立 Work / Edition / Book / Bookshelf / Shelf 基础模型
5. 完成“手动添加一本书 → 图书馆页面显示”完整链路
```

Sprint 1 完成后，我们再进入：

> **Metadata API → AI 识别**

这样开发风险最低，也最容易随时看到成果。

---

## 最终产品一句话定义

> **HomeLib 是一个通过拍照即可批量数字化家庭藏书，并利用 AI 自动完成图书信息补全、标准分类和空间定位的个人家庭图书馆。**

这个版本现在可以作为后续开发的**正式基线**。之后写代码时，原则上不再随意改变核心数据模型和 MVP 边界；新增想法统一放入 V2/V3 Backlog。
