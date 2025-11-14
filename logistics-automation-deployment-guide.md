# 自动化物流情报媒体平台 - 完整部署指南

> **基于技术执行蓝图的企业级实施方案**

---

## 📋 目录

- [I. 系统架构概览](#i-系统架构概览)
- [II. 核心组件部署](#ii-核心组件部署)
- [III. 飞书多维表设计](#iii-飞书多维表设计)
- [IV. n8n工作流配置](#iv-n8n工作流配置)
- [V. AI节点集成](#v-ai节点集成)
- [VI. 人在环路(HITL)流程](#vi-人在环路hitl流程)
- [VII. 成本估算与优化](#vii-成本估算与优化)

---

## I. 系统架构概览

### 🎯 设计哲学

本系统采用**混合智能架构**：
- **程序化过滤** - 快速、免费地过滤90%噪音
- **AI深度分析** - 仅对高质量候选新闻使用昂贵的LLM
- **异步解耦** - 采集、评分、脚本生成完全独立，避免瓶颈
- **人在环路** - AI自动化 + 人工审批，确保内容质量

### 🏗️ 三层架构

```
┌─────────────────────────────────────────────────────────────┐
│          I. 数据采集层 (Data Collection Layer)              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  FreshRSS    │  │  Scrapfly    │  │  n8n HTTP    │      │
│  │  RSS中心     │  │  动态抓取    │  │  API调用     │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│         II. 智能策展层 (AI Curation Layer)                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  规范化      │→ │  分诊评分    │→ │  AI深度评分  │      │
│  │  (Code Node) │  │  (免费)      │  │  (付费)      │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│        III. 内容生产层 (Content Generation Layer)           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  脚本生成    │→ │  人工审批    │→ │  视频制作    │      │
│  │  (异步)      │  │  (飞书)      │  │  (可选)      │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
```

---

## II. 核心组件部署

### 2.1 FreshRSS部署（RSS聚合中心）

#### 为什么需要FreshRSS？
- **集中管理** - 10+个RSS源统一管理，避免n8n轮询开销
- **去重机制** - 内置去重，避免重复拉取
- **API访问** - 提供Google Reader API，n8n一次调用获取所有新闻

#### 部署步骤

**方案A：Docker部署（推荐）**

```bash
# 1. 创建docker-compose.yml
cat > docker-compose.yml << 'EOF'
version: '3'
services:
  freshrss:
    image: freshrss/freshrss:latest
    container_name: freshrss
    ports:
      - "8080:80"
    volumes:
      - ./freshrss_data:/var/www/FreshRSS/data
      - ./freshrss_extensions:/var/www/FreshRSS/extensions
    environment:
      - TZ=Asia/Shanghai
      - CRON_MIN=*/15  # 每15分钟拉取一次RSS
    restart: unless-stopped
EOF

# 2. 启动FreshRSS
docker-compose up -d

# 3. 访问 http://localhost:8080 完成初始化
```

**方案B：云服务器部署**

如果你有VPS（如阿里云、AWS EC2），按照官方文档部署：
https://github.com/FreshRSS/FreshRSS/blob/edge/Docker/README.md

#### 配置FreshRSS

1. **添加RSS源**

登录FreshRSS后，添加以下核心物流RSS：

| RSS名称 | RSS URL |
|---------|---------|
| FreightWaves | `https://www.freightwaves.com/feed` |
| The Loadstar | `https://theloadstar.com/feed/` |
| Journal of Commerce | `https://www.joc.com/rss` |
| SupplyChainBrain | `https://www.supplychainbrain.com/rss` |
| Lloyd's List | `https://www.lloydslist.com/rss` |

2. **启用API访问**

- 进入 `Settings` → `API Management`
- 创建一个API密码
- 记录以下信息：
  - API URL: `http://YOUR_SERVER:8080/api/greader.php`
  - Username: `your_username`
  - Password: `your_api_password`

---

### 2.2 Scrapfly账号配置（动态网页抓取）

#### 为什么需要Scrapfly？
传统的Scrapy无法处理：
- JavaScript渲染的页面（如亚马逊卖家中心）
- 反爬虫保护（如马士基、UPS的企业门户）
- CAPTCHA和浏览器指纹检测

Scrapfly通过云端无头浏览器 + 代理池 + AI提取，一步解决所有问题。

#### 注册与配置

1. **注册账号**
   - 访问 https://scrapfly.io
   - 免费套餐：1000次API调用/月（测试够用）
   - 付费套餐：$29/月起（生产环境推荐）

2. **获取API Key**
   - 登录后台 → API Keys
   - 复制API Key（格式：`scp-live-...`）

3. **测试API调用**

```bash
curl "https://api.scrapfly.io/scrape?key=YOUR_API_KEY&url=https://www.maersk.com/news/category/advisories&asp=true&render_js=true"
```

---

### 2.3 飞书开放平台配置

1. **创建企业自建应用**
   - 登录 https://open.feishu.cn/
   - 创建应用 → 获取 `App ID` 和 `App Secret`

2. **申请权限**
   - 权限管理 → 申请以下权限：
     - `bitable:app` - 多维表格读写
     - `contact:user.base` - 基础用户信息
   - 发布应用版本

3. **创建多维表格（详见第III节）**

---

## III. 飞书多维表设计（任务控制中心）

这是整个系统的"单一事实来源"和"人在环路"界面。

### 表结构设计

在飞书多维表格中创建以下表：

#### 表1：任务控制中心 (Logistics News Hub)

| 字段名称 | 字段类型 | 配置 | 说明 |
|----------|----------|------|------|
| ID | 自动编号 | - | 系统自动生成 |
| News_Title | 多行文本 | - | 新闻标题 |
| Source | 单选 | FreightWaves/Maersk/UPS/MSC/FedEx/Amazon/Shopify/Other | 来源平台 |
| URL | 链接 | - | 原文链接（去重关键字段） |
| Received_At | 日期 | 包含时间 | 采集时间戳 |
| **Status** | 单选 | **Pending/Ready_For_Review/Approved/Rejected/Published** | 🔥人工审批触发器 |
| AI_Triage_Score | 数字 | 精度0 | 程序化分诊分数(0-100) |
| AI_Final_Score | 数字 | 精度1 | AI最终评分(0-10.0) |
| AI_Impact_Score | 数字 | 精度0 | 影响力(1-10) |
| AI_Urgency_Score | 数字 | 精度0 | 紧迫性(1-5) |
| AI_Virality_Score | 数字 | 精度0 | 传播潜力(1-5) |
| AI_Relatability_Score | 数字 | 精度0 | 相关性(1-5) |
| AI_Justification | 多行文本 | - | AI评分理由 |
| AI_Suggested_Hook | 文本 | - | AI建议的钩子 |
| **Generated_Script_v1** | 多行文本 | - | 🔥用户在此编辑脚本 |
| Keywords | 多选 | 罢工/港口/运费/延误/暂停/警报/关税 | AI提取的关键词 |
| Video_URL | 链接 | - | 制作完成的视频链接 |
| Published_At | 日期 | 包含时间 | 发布时间 |
| Notes | 多行文本 | - | 人工备注 |

#### 表2：数据源配置表 (Data Source Config)

用于动态配置采集源，无需修改n8n工作流。

| 字段名称 | 字段类型 | 示例值 |
|----------|----------|--------|
| Source_ID | 自动编号 | 1 |
| Source_Type | 单选 | RSS_Feed/Web_Scrape |
| Source_Name | 文本 | Maersk Advisories |
| Source_URL | 链接 | https://www.maersk.com/news/category/advisories |
| Enabled | 复选框 | ✅ |
| Polling_Frequency | 单选 | 15min/30min/1hour/4hours |
| Priority | 数字 | 1-10 (10最高) |
| Extraction_Prompt | 多行文本 | Extract all advisory items with... |

---

## IV. n8n工作流配置

### 4.1 导入工作流

本项目包含3个核心工作流：

1. **logistics-collection-workflow-v2.json** - 主采集工作流
2. **logistics-script-generation-workflow.json** - 异步脚本生成
3. **logistics-publish-workflow.json** (可选) - 自动发布

#### 导入步骤

```bash
# 1. 登录n8n
# 2. Workflows → Import from File
# 3. 依次导入上述3个JSON文件
```

### 4.2 配置替换清单

打开每个工作流后，按 Ctrl+F 搜索并替换以下占位符：

| 占位符 | 替换为 | 来源 |
|--------|--------|------|
| `YOUR_APP_ID` | `cli_xxxxxx` | 飞书应用凭证 |
| `YOUR_APP_SECRET` | `xxxxxxxx` | 飞书应用凭证 |
| `YOUR_APP_TOKEN` | `bascnxxxxxx` | 飞书多维表格app_token |
| `YOUR_TABLE_ID` | `tblxxxxxx` | 飞书表ID（任务控制中心） |
| `YOUR_SCRAPFLY_API_KEY` | `scp-live-xxxxxx` | Scrapfly API Key |
| `YOUR_FRESHRSS_DOMAIN` | `http://1.2.3.4:8080` | FreshRSS URL |
| `YOUR_CREDENTIAL_ID` | 自动生成 | n8n飞书凭证 |

#### 获取飞书表ID的方法

1. 打开飞书多维表格
2. 查看浏览器地址栏：
   ```
   https://xxx.feishu.cn/base/bascnXXXXXXX?table=tblYYYYYYY
   ```
   - `bascnXXXXXXX` = app_token
   - `tblYYYYYYY` = table_id

### 4.3 工作流详解

#### 工作流1：主采集工作流

**触发频率：** 每15分钟

**核心节点：**

1. **定时触发** - Cron: `*/15 * * * *`
2. **并行采集**
   - FreshRSS API（RSS聚合）
   - Scrapfly API（马士基）
   - Scrapfly API（MSC）
   - Scrapfly API（UPS）
3. **数据规范化** - 统一为canonical_item格式
4. **去重过滤** - 与飞书数据库比对URL
5. **程序化分诊** - 快速打分(0-100)
6. **高分过滤** - 仅保留 >50分的新闻
7. **AI摘要生成** (需配置)
8. **AI深度评分** (需配置，JSON模式)
9. **写入飞书** - 状态为"Pending"

**成本估算（每天）：**
- 程序化过滤：96次运行 × 100条新闻 = 9,600条
- AI摘要调用：~10条（90%被过滤）
- AI评分调用：~10条
- **总AI调用：~20次/天**

---

#### 工作流2：脚本生成工作流

**触发方式：** Webhook（由主工作流或飞书自动化触发）

**核心节点：**

1. **Webhook触发器** - 接收高分新闻数据
2. **分数过滤** - 仅处理 final_score > 8.0
3. **脚本提示词构建** - 4部分结构（Hook-Body-CTA）
4. **AI脚本生成** (需配置GPT-4或Claude-Opus)
5. **更新飞书** - 写入 Generated_Script_v1 字段
6. **返回响应**

**触发示例（主工作流末尾添加）：**

```javascript
// 在主工作流的最后一个节点后添加HTTP Request节点
if ($json.ai_final_score > 8.0) {
  return {
    json: {
      url: 'YOUR_N8N_WEBHOOK_URL/logistics-script-trigger',
      method: 'POST',
      body: $json
    }
  };
}
```

---

## V. AI节点集成

### 5.1 方案选择

| AI服务 | 推荐模型 | 成本 | 适用场景 |
|--------|----------|------|----------|
| **OpenAI** | gpt-4o-mini | $0.15/1M tokens | 摘要生成 |
| **OpenAI** | gpt-4o | $5/1M tokens | 脚本生成（需创意） |
| **Google Gemini** | gemini-1.5-flash | 免费（60 RPM） | 评分（JSON模式） |
| **Anthropic Claude** | claude-3-haiku | $0.25/1M tokens | 摘要+评分 |

### 5.2 替换AI占位节点

#### 步骤1：添加OpenAI凭证

1. n8n → Credentials → New
2. 选择 `OpenAI API`
3. 输入API Key（从 https://platform.openai.com/api-keys 获取）

#### 步骤2：替换"AI摘要"节点

删除占位节点，添加：

**节点类型：** `OpenAI`

**配置：**
```
Resource: Chat
Model: gpt-4o-mini
Prompt: {{ $json.ai_summary_prompt }}
Options:
  - Max Tokens: 200
  - Temperature: 0.3
```

#### 步骤3：替换"AI深度评分"节点（关键！）

**使用Google Gemini的JSON模式：**

**节点类型：** `Google Gemini`

**配置：**
```
Operation: Text
Model: gemini-1.5-flash
Prompt: {{ $json.ai_scoring_prompt }}
Options:
  - response_mime_type: application/json
  - response_schema:
    {
      "type": "object",
      "properties": {
        "impact_score": {"type": "number"},
        "urgency_score": {"type": "number"},
        "virality_score": {"type": "number"},
        "relatability_score": {"type": "number"},
        "final_score": {"type": "number"},
        "justification": {"type": "string"},
        "suggested_hook": {"type": "string"}
      },
      "required": ["impact_score", "urgency_score", "virality_score", "relatability_score", "final_score", "justification", "suggested_hook"]
    }
```

**为什么使用JSON Schema？**
- 强制AI返回结构化输出
- 避免解析错误
- 确保后续节点能正确读取字段

#### 步骤4：替换"AI脚本生成"节点

**节点类型：** `OpenAI`

**配置：**
```
Resource: Chat
Model: gpt-4o (需要更强的创意能力)
Prompt: {{ $json.script_generation_prompt }}
Options:
  - Max Tokens: 800
  - Temperature: 0.7
```

---

## VI. 人在环路(HITL)流程

### 6.1 日常工作流程

**上午9:00 - 打开飞书仪表盘**

1. 打开"任务控制中心"表
2. 创建视图过滤器：
   ```
   - Status = "Pending" 或 "Ready_For_Review"
   - AI_Final_Score >= 8.0
   - 排序：AI_Final_Score 降序
   ```

3. 你将看到当天5-10条"最佳"新闻候选

**审批流程：**

1. **阅读内容**
   - 查看 `News_Title`、`AI_Justification`
   - 点击 `URL` 查看原文

2. **编辑脚本**
   - 直接在 `Generated_Script_v1` 字段中修改
   - 调整语气、数字、钩子

3. **批准发布**
   - 将 `Status` 从 "Pending" 改为 **"Approved"**

4. **（可选）触发自动化**
   - 当Status变为"Approved"时，飞书自动化会触发视频制作流程

### 6.2 配置飞书自动化（可选）

**目标：** 当用户批准新闻时，自动触发视频制作API

#### 步骤

1. **在飞书表格中创建自动化**
   - 进入"任务控制中心"表
   - 点击右上角 "自动化"
   - 新建自动化

2. **配置触发器**
   ```
   When: 字段值变更
   字段: Status
   条件: 变更为 "Approved"
   ```

3. **配置动作**
   ```
   Then: 发送HTTP请求
   Method: POST
   URL: YOUR_N8N_WEBHOOK_URL/logistics-publish-trigger
   Headers: Content-Type: application/json
   Body:
   {
     "record_id": "{{record_id}}",
     "title": "{{News_Title}}",
     "script": "{{Generated_Script_v1}}",
     "hook": "{{AI_Suggested_Hook}}"
   }
   ```

---

## VII. 成本估算与优化

### 7.1 月度成本分解

**假设：** 每天处理100条新闻，10条进入AI评分，2条生成脚本

| 成本项 | 单价 | 用量/月 | 月成本 |
|--------|------|---------|--------|
| **FreshRSS (VPS)** | $5/月 | 1台 | $5 |
| **Scrapfly** | $29/月 | 基础套餐 | $29 |
| **OpenAI (摘要)** | $0.15/1M tokens | ~300K tokens | $0.05 |
| **Gemini (评分)** | 免费 | 300次/月 | $0 |
| **OpenAI (脚本)** | $5/1M tokens | ~60K tokens | $0.30 |
| **飞书** | 免费 | - | $0 |
| **n8n** | 自托管/$20 | 1个实例 | $0-20 |
| **总计** | - | - | **$34.35 - $54.35** |

### 7.2 成本优化策略

#### 策略1：使用Gemini Flash替代OpenAI

Gemini 1.5 Flash有60次/分钟的免费配额，足够小规模使用。

**节省：** $0.35/月（几乎全免）

#### 策略2：降低采集频率

将主工作流从每15分钟改为每30分钟：
- 节省50% Scrapfly API调用
- **节省：** $14.5/月

#### 策略3：自建Scrapfly替代方案

使用开源方案：
- **Playwright** (无头浏览器)
- **Bright Data** 代理服务 ($0.6/GB)
- **Capsolver** (验证码服务)

适合月采集量>10,000次的场景。

---

## VIII. 高级功能扩展

### 8.1 集成视频自动生成API

可选集成：
- **HeyGen** - AI数字人视频生成
- **Pictory.ai** - 文本转视频
- **ElevenLabs** - 文字转语音

### 8.2 添加更多数据源

在"数据源配置表"中新增：

| 来源 | URL | 抓取方法 |
|------|-----|----------|
| DHL Alerts | https://www.dhl.com/global-en/home/tracking/tracking-global-forwarding.html | Scrapfly |
| CMA CGM (US) | https://www.cma-cgm.com/local/united-states/all-news | Scrapfly |
| Shopify Changelog | https://changelog.shopify.com/ | Scrapfly |
| Amazon Seller News | https://sell.amazon.com/blog/announcements | Scrapfly |

### 8.3 多语言支持

在AI提示词中添加：
```
请用[中文/英文]输出...
```

---

## IX. 故障排查

### 常见问题

**Q1: FreshRSS拉取RSS失败**

**A:** 检查：
1. RSS URL是否正确（用浏览器测试）
2. 服务器能否访问外网
3. FreshRSS Cron是否运行（`docker logs freshrss`）

**Q2: Scrapfly返回403/429错误**

**A:**
- 403: 需要启用 `asp=true`（反爬绕过）
- 429: API配额用完，升级套餐或降低频率

**Q3: AI节点返回非JSON格式**

**A:**
- 必须使用Gemini的JSON模式或OpenAI的`response_format: {type: "json_object"}`
- 在提示词中明确要求："仅返回JSON，不要包含任何其他文本"

**Q4: 飞书写入失败**

**A:**
- 检查字段名称是否完全匹配（区分大小写）
- 检查数据类型（文本 vs 数字 vs 日期）
- 检查Token是否过期（每2小时过期一次）

---

## X. 部署检查清单

在上线前，确保完成以下步骤：

### ✅ 基础设施
- [ ] FreshRSS已部署并运行
- [ ] Scrapfly账号已注册，API Key已获取
- [ ] 飞书应用已创建，权限已申请
- [ ] 飞书多维表已创建（表1+表2）
- [ ] n8n已安装（自托管或云版本）

### ✅ 工作流配置
- [ ] 主采集工作流已导入
- [ ] 脚本生成工作流已导入
- [ ] 所有占位符已替换（App ID, API Key等）
- [ ] FreshRSS已添加10+个RSS源
- [ ] Scrapfly测试调用成功

### ✅ AI集成
- [ ] OpenAI/Gemini凭证已配置
- [ ] AI摘要节点已替换并测试
- [ ] AI评分节点已启用JSON模式
- [ ] AI脚本生成节点已替换

### ✅ 测试运行
- [ ] 主工作流手动触发 → 飞书表有数据
- [ ] 检查 `AI_Final_Score` 是否正确计算
- [ ] 触发脚本生成 → `Generated_Script_v1` 有内容
- [ ] 人工审批 → Status变更 → 自动化触发

---

## XI. 联系与支持

如有问题，请检查：
1. n8n执行日志（Executions标签）
2. 飞书API响应（HTTP Request节点输出）
3. AI节点返回内容（是否为有效JSON）

---

## 附录A：完整数据流图

```
┌──────────────┐
│  15分钟触发   │
└──────┬───────┘
       │
       ├────────────────┐
       │                │
┌──────▼───────┐  ┌────▼──────────┐
│ FreshRSS API │  │ Scrapfly APIs │
│  (RSS源)     │  │ (动态抓取)    │
└──────┬───────┘  └────┬──────────┘
       │                │
       └────────┬───────┘
                │
         ┌──────▼──────┐
         │ 数据规范化   │ ← 关键步骤
         └──────┬──────┘
                │
         ┌──────▼──────┐
         │ 飞书去重检查 │
         └──────┬──────┘
                │
         ┌──────▼──────┐
         │ 分诊评分     │ ← 免费，过滤90%
         │ (程序化)     │
         └──────┬──────┘
                │
         ┌──────▼──────┐
         │  >50分过滤   │
         └──────┬──────┘
                │ (仅10%通过)
                │
         ┌──────▼──────┐
         │  AI摘要      │ ← 付费
         └──────┬──────┘
                │
         ┌──────▼──────┐
         │  AI深度评分  │ ← 付费，JSON模式
         └──────┬──────┘
                │
         ┌──────▼──────┐
         │ 写入飞书表   │ Status: Pending
         └──────┬──────┘
                │
       ┌────────┴────────┐
       │                 │
┌──────▼──────┐   ┌──────▼──────────┐
│ >8.0分自动   │   │  人工审批       │
│ 触发脚本生成 │   │  (飞书仪表盘)   │
└──────┬──────┘   └──────┬──────────┘
       │                 │
       │         ┌───────▼─────────┐
       │         │ Status: Approved │
       │         └───────┬─────────┘
       │                 │
       └─────────┬───────┘
                 │
          ┌──────▼──────┐
          │ AI脚本生成   │ (异步工作流)
          └──────┬──────┘
                 │
          ┌──────▼──────┐
          │ 更新飞书表   │ Ready_For_Review
          └──────┬──────┘
                 │
          ┌──────▼──────┐
          │  人工编辑   │
          │  +批准发布  │
          └──────┬──────┘
                 │
          ┌──────▼──────┐
          │ 视频制作     │ (可选自动化)
          └─────────────┘
```

---

**祝你的自动化物流媒体平台成功上线！** 🚀
