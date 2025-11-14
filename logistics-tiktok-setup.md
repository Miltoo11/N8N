# 物流资讯TikTok自动化工作流 - 配置指南

## 📋 概述

这个工作流每周自动从全球物流媒体拉取最新资讯，通过AI生成TikTok新闻脚本，帮助你快速制作无口播的新闻风格短视频。

---

## 🎯 工作流程图

```
定时触发(每周一9AM)
    ↓
获取飞书Token
    ↓
读取配置表(RSS源+关键词)
    ↓
并行拉取多个RSS feeds
    ↓
解析XML → 提取新闻
    ↓
关键词过滤 + 时间过滤(7天内)
    ↓
去重合并
    ↓
AI生成摘要 + TikTok脚本
    ↓
计算热度评分
    ↓
写入飞书数据表(按热度排序)
```

---

## 📊 需要创建的飞书表格

### 1️⃣ **配置表** (Config)

| 字段名 | 字段类型 | 说明 | 示例值 |
|--------|----------|------|--------|
| config_key | 文本 | 配置键 | `rss_feeds` |
| config_value | 文本 | 配置值 | 见下方详细配置 |

#### 配置项说明：

| config_key | config_value 示例 | 说明 |
|------------|-------------------|------|
| `rss_feeds` | `https://feeds.feedburner.com/logisticsmgmt/latest\|https://www.supplychainbrain.com/rss` | RSS源列表，用\|分隔 |
| `keywords` | `供应链\|物流\|航运\|港口\|海运\|空运\|跨境\|清关\|仓储` | 关键词，用\|分隔 |
| `days_back` | `7` | 拉取最近N天的新闻 |
| `max_items_per_source` | `20` | 每个RSS源最多拉取N条 |
| `ai_model` | `gpt-4o-mini` | AI模型 |
| `ai_prompt_summary` | `请用50字以内总结这条物流新闻的核心要点` | AI摘要提示词 |
| `ai_prompt_tiktok` | `请将这条物流新闻改写成60秒TikTok新闻播报脚本，使用滚动字幕形式，语言简洁有力，突出数字和关键事实` | AI脚本生成提示词 |

---

### 2️⃣ **新闻数据表** (Logistics News)

| 字段名 | 字段类型 | 说明 |
|--------|----------|------|
| title | 文本 | 新闻标题 |
| description | 文本 | 新闻描述 |
| link | 超链接 | 原文链接 |
| source | 文本 | 来源媒体 |
| pub_date | 日期 | 发布日期 |
| ai_summary | 文本 | AI生成的摘要 |
| tiktok_script | 文本 | TikTok脚本 |
| hotness_score | 数字 | 热度评分(0-100) |
| hot_level | 单选 | 热度等级(Low/Medium/High/🔥极热) |
| status | 单选 | 状态(pending_ai/ready_for_production/in_production/published) |
| video_url | 超链接 | 制作完成的视频链接(手动填写) |
| created_time | 创建时间 | 自动生成 |

---

## 🌐 推荐的RSS数据源

### 英文物流媒体（国际视角）

| 媒体名称 | RSS链接 | 覆盖领域 |
|----------|---------|----------|
| Logistics Management | `https://feeds.feedburner.com/logisticsmgmt/latest` | 综合物流 |
| SupplyChainBrain | `https://www.supplychainbrain.com/rss` | 供应链管理 |
| FreightWaves | `https://www.freightwaves.com/feed` | 货运、航运 |
| Journal of Commerce | `https://www.joc.com/rss` | 国际贸易物流 |
| Lloyd's List | `https://www.lloydslist.com/rss` | 航运 |

### 中文物流媒体（本土视角）

| 媒体名称 | RSS/来源 | 说明 |
|----------|---------|------|
| 物流时代周刊 | 需手动配置API | 中国物流行业 |
| 运联智库 | 需手动配置 | 物流科技 |
| 罗戈网 | `http://www.logclub.com/rss` | 物流资讯 |

---

## 🤖 AI节点配置说明

**⚠️ 重要提示：**
工作流中的 `AI生成内容（占位）` 节点需要替换成真实的AI节点：

### 方案A：使用OpenAI节点

1. 在n8n中添加 **OpenAI** 节点
2. 配置参数：
   - Model: `gpt-4o-mini`
   - Prompt:
     ```
     请根据以下物流新闻生成：
     1. 50字摘要
     2. 60秒TikTok新闻播报脚本（滚动字幕形式）

     新闻内容：
     标题：{{ $json.title }}
     正文：{{ $json.description }}
     ```

### 方案B：使用Claude节点（更便宜）

1. 添加 **Anthropic** 节点
2. Model: `claude-3-haiku-20240307`
3. 提示词同上

---

## 🎬 TikTok视频制作建议

### 对标账号参考

- **CNN** (@cnn)
- **BBC News** (@bbcnews)
- **Bloomberg** (@business)

### 制作流程

1. **从飞书表拉取当周热度Top 7的新闻**
2. **使用剪映/CapCut模板：**
   - 背景：深蓝/黑色 + 世界地图动画
   - 字幕：白色大字 + 滚动效果
   - 配乐：新闻感背景音乐
   - 时长：60秒/条
3. **发布频率：** 每周3-5条

### TikTok脚本示例

```
📢 全球物流快讯 | 11月第2周

🚢 马士基宣布暂停红海航线
受也门胡塞武装袭击影响
全球最大航运公司马士基决定
暂停所有途经红海的集装箱船

影响：
• 欧亚航线延长10-14天
• 运费预计上涨15-20%
• 全球供应链再次承压

来源：Lloyd's List
```

---

## 🔧 工作流部署步骤

### 1. 准备飞书环境

1. 登录飞书开放平台 https://open.feishu.cn/
2. 创建企业自建应用
3. 获取 `App ID` 和 `App Secret`
4. 创建飞书多维表，按上方表结构建表
5. 获取 `app_token` 和 `table_id`

### 2. 导入工作流

1. 打开n8n
2. 导入 `logistics-tiktok-workflow.json`
3. 替换以下占位符：
   - `YOUR_APP_ID` → 你的飞书App ID
   - `YOUR_APP_SECRET` → 你的飞书App Secret
   - `YOUR_APP_TOKEN` → 飞书多维表app_token
   - `YOUR_CONFIG_TABLE_ID` → 配置表table_id
   - `YOUR_TABLE_ID` → 新闻数据表table_id
   - `YOUR_CREDENTIAL_ID` → n8n飞书凭证ID

### 3. 配置AI节点

- 删除占位节点 `AI生成内容（占位）`
- 添加 OpenAI 或 Claude 节点
- 连接到 `添加哈希字段` 和 `计算热度评分` 之间

### 4. 测试运行

1. 先在配置表填入1-2个RSS源测试
2. 手动触发工作流
3. 检查飞书表是否正确写入数据

### 5. 启用定时触发

- 默认：每周一早上9:00运行
- 可修改cron表达式调整频率

---

## 📈 热度评分算法

```javascript
热度总分 (0-100) = 时效性(40分) + 关键词匹配度(30分) + 内容丰富度(30分)

时效性：
- 24小时内：40分
- 48小时内：30分
- 72小时内：20分
- 更早：10分

关键词匹配度：
- 每匹配1个关键词：+10分（上限30分）

内容丰富度：
- 内容>500字：30分
- 内容>300字：20分
- 其他：10分

热度等级：
- 🔥极热：≥80分
- High：60-79分
- Medium：40-59分
- Low：<40分
```

---

## 🛠️ 高级优化建议

### 1. 添加更多数据源

```javascript
// 在配置表的 rss_feeds 中追加
https://www.dcvelocity.com/rss/headlines/
https://www.inboundlogistics.com/cms/rss/
```

### 2. 集成图片/视频素材库

- 使用 Pexels/Unsplash API 自动搜索相关图片
- 关键词：shipping, logistics, warehouse, cargo

### 3. 自动发布到TikTok

- 使用 TikTok API（需企业认证）
- 或集成 Make.com/Zapier 的TikTok连接器

### 4. 添加人工审核环节

在 `写入飞书数据表` 后添加：
- **飞书审批流**：编辑可在飞书中标记"通过/拒绝"
- **Slack通知**：每周发送待审核列表

---

## 🔍 常见问题

### Q1: RSS源拉取失败怎么办？

**A:** 检查：
1. RSS URL是否正确
2. 网络是否可访问（可能需要代理）
3. 增加 HTTP Request 节点的超时时间

### Q2: AI生成的脚本不理想？

**A:** 优化提示词：
```
你是一位专业的物流行业新闻编辑。请将以下新闻改写成TikTok短视频脚本：

要求：
1. 时长控制在60秒（约200字）
2. 使用新闻播报语气，简洁有力
3. 突出数字、地名、公司名等关键信息
4. 用emoji增强可读性（📢🚢✈️📦等）
5. 结尾给出新闻来源

新闻内容：
标题：{{ $json.title }}
正文：{{ $json.description }}
```

### Q3: 如何避免重复内容？

**A:** 工作流已内置去重：
- 基于标题前100字符去重
- 可在飞书表中添加 `content_hash` 字段进一步验证

---

## 📞 支持

如有问题，请检查：
1. n8n执行日志
2. 飞书API响应
3. AI节点调用记录

---

## 🎉 下一步

1. **导入工作流** → 替换占位符 → 测试
2. **建飞书表** → 填配置 → 运行
3. **拿到数据** → 制作视频 → 发布TikTok
4. **持续优化** → 调整关键词 → 迭代提示词

祝你的TikTok物流账号爆款连连！🚀
