# Google Sheets 输出字段完整说明

## ✅ 问题已修复

您反馈的所有必需字段现在都已经正确映射到Google Sheets输出。

---

## 📋 您需要的12个字段（全部已包含）

| # | 字段名 | 数据源 | 说明 |
|---|--------|--------|------|
| 1 | **关键词** | `keyword` | 来自交叉匹配引擎 |
| 2 | **链接** | `permalink` | Reddit帖子完整URL |
| 3 | **行业** | `keyword_category` 或 `subreddit_classification` | 关键词类别或频道分类 |
| 4 | **频道** | `subreddit` | Reddit频道名 |
| 5 | **标题** | `title` | 帖子标题 |
| 6 | **原文** | `selftext` | 帖子正文内容 |
| 7 | **热度前十评论** | `热门评论文本` | 前10条热评格式化文本 |
| 8 | **作者** | `author` | Reddit用户名 |
| 9 | **主题/类别** | `主题类别` | AI分析的主题分类 |
| 10 | **转化潜力** | `转化潜力` | AI评估：高/中/低 |
| 11 | **comments_api_url** | `comments_api` | Reddit评论API链接 |
| 12 | **api_url** | `url` | Reddit原始链接 |

---

## 📊 完整输出字段列表（37个）

### 基础信息（16个字段）

| 字段名 | 类型 | 示例 | 说明 |
|--------|------|------|------|
| **关键词** | 文本 | "logistics" | 搜索关键词 |
| **链接** | URL | "https://reddit.com/r/..." | 帖子链接 |
| **行业** | 文本 | "物流", "电商" | 关键词类别或频道分类 |
| **平台** | 文本 | "Reddit" | 固定值 |
| **频道** | 文本 | "Entrepreneur" | Reddit subreddit |
| **post_id** | 文本 | "abc123xyz" | 唯一帖子ID |
| **score** | 数字 | 156 | 点赞数（upvotes） |
| **upvote_ratio** | 小数 | 0.95 | 点赞率（0-1） |
| **评论数** | 数字 | 42 | 评论总数 |
| **post发布日期** | 日期 | "2025-01-15" | 发布日期 |
| **标题** | 文本 | "How to ship to..." | 帖子标题 |
| **原文** | 长文本 | "I'm looking for..." | 帖子正文 |
| **热度前十评论** | 长文本 | "1. @user1 (50👍)..." | 前10条评论格式化 |
| **作者** | 文本 | "username123" | Reddit用户名 |
| **comments_api_url** | URL | "https://oauth.reddit..." | 评论API链接 |
| **api_url** | URL | "https://reddit.com/..." | 原始链接 |

### AI分析字段（11个）

| 字段名 | 类型 | 示例 | 说明 |
|--------|------|------|------|
| **情绪分析** | 文本 | "正面", "负面", "中性" | Gemini分析结果 |
| **情绪分析分数** | 数字 | 75 | 0-100分 |
| **痛点** | 文本 | "运输成本过高" | 用户痛点 |
| **用户需求** | 文本 | "寻找便宜的物流方案" | 隐含需求 |
| **竞对提及** | 文本 | "DHL, FedEx" | 提及的竞争对手 |
| **紧急程度** | 文本 | "高", "中", "低" | 需求紧急度 |
| **主题类别** | 文本 | "物流", "清关", "仓储" | 话题分类 |
| **商业机会** | 文本 | "提供低成本物流服务" | 潜在商机 |
| **转化潜力** | 文本 | "高", "中", "低" | 转化可能性 |
| **seo关键词** | 文本 | "international shipping..." | 英文SEO关键词 |
| **中文总结** | 文本 | "用户寻找国际物流方案..." | 100字以内总结 |

### 社交媒体创意（7个）

| 字段名 | 类型 | 说明 |
|--------|------|------|
| **linkedin创意** | 长文本 | LinkedIn专业文案 |
| **twitter创意** | 文本 | 280字符英文推文 |
| **facebook创意** | 长文本 | 中文Facebook贴文 |
| **instagram创意** | 文本 | IG带话题标签文案 |
| **tiktok创意** | 长文本 | 15秒短视频脚本 |
| **youtube标题** | 文本 | 吸引点击的标题 |
| **blog标题** | 文本 | SEO优化的博客标题 |

### 热度指标（3个）

| 字段名 | 类型 | 示例 | 说明 |
|--------|------|------|------|
| **热度分数** | 数字 | 125.67 | 综合热度分数 |
| **趋势** | 文本 | "上升", "平稳" | 趋势标签 |
| **互动率** | 百分比 | "26.92%" | 评论/点赞比率 |

---

## 🔍 数据来源追踪

### 关键词 & 频道优先级
```
读取关键词表 → 交叉匹配引擎 → ... → 最终输出
  ↓
keyword, keyword_priority, keyword_category

读取频道表 → 交叉匹配引擎 → ... → 最终输出
  ↓
subreddit, subreddit_priority, subreddit_classification
```

### 行业字段
```
行业 = keyword_category || subreddit_classification
```
- 优先使用关键词类别
- 如果为空则使用频道分类

### 热度前十评论
```
提取数据和时间过滤 → 抓取Reddit热评 → 处理评论数据 → 合并AI分析结果
                                      ↓
                              热门评论文本 → 热度前十评论
```

格式示例：
```
1. @user1 (50👍 2025-01-15):
This is a great post...

2. @user2 (35👍 2025-01-15):
I agree with this...
```

### 主题/类别
```
数据时间过滤 → Gemini分析HTTP → 合并AI分析结果
                    ↓
                AI生成 → 主题类别
```
- AI分析结果中的 `topic_category` 或 `主题/类别`

### 转化潜力
```
Gemini分析HTTP → 合并AI分析结果
      ↓
AI生成 → 转化潜力 (高/中/低)
```

### API链接
```
提取数据和时间过滤节点生成:
- comments_api: https://oauth.reddit.com/comments/{post_id}.json
- url: Reddit原始链接或permalink
```

---

## 📈 数据示例

### 完整行示例

| 字段 | 值 |
|------|-----|
| 关键词 | logistics |
| 链接 | https://reddit.com/r/Entrepreneur/comments/abc123 |
| 行业 | 物流 |
| 平台 | Reddit |
| 频道 | Entrepreneur |
| post_id | abc123xyz |
| score | 156 |
| upvote_ratio | 0.95 |
| 评论数 | 42 |
| post发布日期 | 2025-01-15 |
| 标题 | How to ship products to Europe cheaply? |
| 原文 | I'm looking for affordable shipping options... |
| 热度前十评论 | 1. @user1 (50👍 2025-01-15): Try DHL... |
| 作者 | entrepreneur123 |
| comments_api_url | https://oauth.reddit.com/comments/abc123.json |
| api_url | https://reddit.com/r/Entrepreneur/comments/abc123 |
| 情绪分析 | 中性 |
| 情绪分析分数 | 60 |
| 痛点 | 国际运输成本过高 |
| 用户需求 | 寻找经济实惠的欧洲运输方案 |
| 竞对提及 | DHL, FedEx, UPS |
| 紧急程度 | 中 |
| 主题类别 | 国际物流 |
| 商业机会 | 提供中小企业定制物流服务 |
| 转化潜力 | 中 |
| seo关键词 | international shipping, europe, affordable |
| 中文总结 | 创业者寻找经济实惠的欧洲物流解决方案... |
| linkedin创意 | 🌍 Struggling with high shipping costs?... |
| twitter创意 | Looking for affordable shipping to Europe?... |
| facebook创意 | 跨境卖家们！是不是被高昂的运费困扰？... |
| instagram创意 | 📦✈️ 国际运输不该这么贵！... #跨境电商 |
| tiktok创意 | 画面：包裹堆积如山 旁白：运费太贵了... |
| youtube标题 | How I Cut My Europe Shipping Costs By 40% |
| blog标题 | 中小企业欧洲物流成本优化完全指南 |
| 热度分数 | 125.67 |
| 趋势 | 上升 |
| 互动率 | 26.92% |

---

## ✅ 验证清单

运行工作流后，请检查Google Sheets：

### 必有字段（不能为空）
- [ ] ✅ 关键词 - 每行都有值
- [ ] ✅ 链接 - 每行都有Reddit链接
- [ ] ✅ 频道 - 每行都有subreddit名称
- [ ] ✅ 标题 - 每行都有帖子标题
- [ ] ✅ post_id - 每行都有唯一ID

### 应有字段（可能为空）
- [ ] ✅ 行业 - 有关键词类别或频道分类
- [ ] ✅ 原文 - 如果是纯文本帖会有内容
- [ ] ✅ 热度前十评论 - 如果有评论会显示
- [ ] ✅ 作者 - Reddit用户名
- [ ] ✅ 主题/类别 - AI分析结果
- [ ] ✅ 转化潜力 - 高/中/低
- [ ] ✅ comments_api_url - API链接
- [ ] ✅ api_url - Reddit链接

### AI生成字段（Gemini成功时有值）
- [ ] ✅ 情绪分析
- [ ] ✅ 痛点
- [ ] ✅ 用户需求
- [ ] ✅ linkedin创意
- [ ] ✅ twitter创意
- [ ] ✅ 中文总结

---

## 🔧 故障排除

### 问题1：某些字段完全没有（整列空白）

**可能原因：**
1. 上游节点数据丢失
2. 字段命名不匹配

**解决方法：**
```python
# 检查"合并AI分析结果"节点代码
# 确认包含所有字段映射：
关键词: data.keyword || '',
链接: data.permalink || '',
行业: data.keyword_category || data.subreddit_classification || '',
...
```

### 问题2：行业字段为空

**原因：** 关键词表和频道表都没有提供类别/分类信息

**解决方法：**
1. 在关键词表添加"类别"列
2. 或在频道表添加"分类"列

### 问题3：热度前十评论为空

**原因：**
- 帖子没有评论
- 评论API调用失败
- "处理评论数据"节点未继承上游数据

**解决方法：**
1. 检查"处理评论数据"节点是否包含 `$items("提取数据和时间过滤")`
2. 查看节点执行日志

### 问题4：AI分析字段为空

**原因：**
- Gemini API调用失败
- API返回格式不正确
- 超过速率限制

**解决方法：**
1. 检查Gemini API凭证
2. 查看"Gemini分析HTTP"节点日志
3. 降低批处理速度（增加等待时间）

---

## 📝 字段映射代码参考

在"合并AI分析结果"节点中的核心映射逻辑：

```javascript
output.push({
  // 继承所有上游字段
  ...data,

  // 您需要的12个字段
  关键词: data.keyword || '',
  链接: data.permalink || '',
  行业: data.keyword_category || data.subreddit_classification || '',
  平台: 'Reddit',
  频道: data.subreddit || data.subreddit_actual || '',
  标题: data.title || '',
  原文: data.selftext || '',
  热度前十评论: data.热门评论文本 || '',
  作者: data.author || '',
  主题类别: aiAnalysis.topic_category || aiAnalysis['主题/类别'] || '',
  转化潜力: aiAnalysis.conversion_potential || aiAnalysis['转化潜力'] || '低',
  comments_api_url: data.comments_api || '',
  api_url: data.url || data.permalink || '',

  // AI分析字段
  情绪分析: aiAnalysis.sentiment || '未分析',
  痛点: aiAnalysis.pain_points || '',
  用户需求: aiAnalysis.user_needs || '',
  // ... 其他AI字段

  // 社交媒体创意
  linkedin创意: aiAnalysis.linkedin创意 || '',
  twitter创意: aiAnalysis.twitter创意 || '',
  // ... 其他社交媒体字段

  // 热度指标
  热度分数: data.final_hot_score || 0,
  趋势: (data.score || 0) > 100 ? '上升' : '平稳',
  互动率: Math.round((data.engagement_rate || 0) * 10000) / 100 + '%'
});
```

---

## 🎯 总结

### ✅ 已包含的所有必需字段

| 状态 | 字段 |
|------|------|
| ✅ | 关键词 |
| ✅ | 链接 |
| ✅ | 行业 |
| ✅ | 频道 |
| ✅ | 标题 |
| ✅ | 原文 |
| ✅ | 热度前十评论 |
| ✅ | 作者 |
| ✅ | 主题/类别 |
| ✅ | 转化潜力 |
| ✅ | comments_api_url |
| ✅ | api_url |

### 📊 输出统计

- **基础字段**: 16个
- **AI分析字段**: 11个
- **社交媒体创意**: 7个
- **热度指标**: 3个
- **总计**: 37个字段

---

**更新时间**: 2025-01-XX
**版本**: v2.2 (完整字段映射版)
**状态**: ✅ 所有必需字段已包含
