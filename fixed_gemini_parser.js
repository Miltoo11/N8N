// =======================================================
// 🧩 Gemini JSON 解析器 - 简化版（保证输出）
// 功能：解析Gemini API响应，输出标准化的18个字段
// =======================================================

const input = $json;

// --- 1. 保留 row_number ---
const row_number = $json.row_number || null;

// --- 2. 提取 Gemini 响应文本 ---
let rawText = "";
try {
  rawText = input.candidates?.[0]?.content?.parts?.[0]?.text || "";
} catch (e) {
  console.log("❌ 无法提取Gemini响应文本");
}

if (!rawText) {
  console.log("⚠️ Gemini响应为空");
  return {
    json: {
      row_number,
      情绪分析: "",
      情绪分析分数: 0,
      痛点: "",
      用户需求: "",
      竞对提及: "",
      紧急程度: "",
      "主题/类别": "",
      商业机会: "",
      转化潜力: "",
      seo关键词: "",
      中文总结: "",
      linkedin创意: "",
      twitter创意: "",
      facebook创意: "",
      instagram创意: "",
      tiktok创意: "",
      youtube标题: "",
      blog标题: ""
    }
  };
}

// --- 3. 清理文本（移除markdown标记） ---
let cleaned = rawText
  .replace(/```json/gi, "")
  .replace(/```/g, "")
  .trim();

// --- 4. 提取JSON对象 ---
let parsed = null;
const jsonStart = cleaned.indexOf("{");
const jsonEnd = cleaned.lastIndexOf("}");

if (jsonStart !== -1 && jsonEnd !== -1 && jsonEnd > jsonStart) {
  try {
    const jsonStr = cleaned.slice(jsonStart, jsonEnd + 1);
    parsed = JSON.parse(jsonStr);
    console.log("✅ JSON解析成功");
  } catch (err) {
    console.log("❌ JSON解析失败:", err.message);
    console.log("原始文本:", cleaned.slice(0, 200));
  }
}

if (!parsed || typeof parsed !== 'object') {
  console.log("⚠️ 无有效JSON对象");
  return {
    json: {
      row_number,
      情绪分析: "",
      情绪分析分数: 0,
      痛点: "",
      用户需求: "",
      竞对提及: "",
      紧急程度: "",
      "主题/类别": "",
      商业机会: "",
      转化潜力: "",
      seo关键词: "",
      中文总结: "",
      linkedin创意: "",
      twitter创意: "",
      facebook创意: "",
      instagram创意: "",
      tiktok创意: "",
      youtube标题: "",
      blog标题: ""
    }
  };
}

// --- 5. 字段映射规则 ---
// 支持多种可能的字段名称（中文、英文、带前缀等）
function getValue(obj, ...keys) {
  for (const key of keys) {
    if (obj[key] !== undefined && obj[key] !== null) {
      return obj[key];
    }
  }
  return "";
}

// --- 6. 递归搜索字段（处理嵌套结构） ---
function findValue(obj, targetKeys) {
  // 直接查找
  for (const key of targetKeys) {
    if (obj[key] !== undefined && obj[key] !== null) {
      return obj[key];
    }
  }

  // 递归搜索子对象
  for (const value of Object.values(obj)) {
    if (typeof value === 'object' && value !== null && !Array.isArray(value)) {
      const found = findValue(value, targetKeys);
      if (found !== "") return found;
    }
  }

  return "";
}

// --- 7. 标准化输出（18个字段） ---
const output = {
  row_number: row_number,

  // 字段1: 情绪分析
  情绪分析: findValue(parsed, [
    "情绪分析", "sentiment", "情感分析",
    "AI分析字段.情绪分析"
  ]),

  // 字段2: 情绪分析分数
  情绪分析分数: parseInt(findValue(parsed, [
    "情绪分析分数", "sentiment_score", "情绪分数", "情感分数",
    "AI分析字段.情绪分析分数"
  ])) || 0,

  // 字段3: 痛点
  痛点: findValue(parsed, [
    "痛点", "pain_points", "用户痛点",
    "AI分析字段.痛点"
  ]),

  // 字段4: 用户需求
  用户需求: findValue(parsed, [
    "用户需求", "user_needs", "需求",
    "AI分析字段.用户需求"
  ]),

  // 字段5: 竞对提及
  竞对提及: findValue(parsed, [
    "竞对提及", "competitor_mention", "竞品提及",
    "AI分析字段.竞对提及"
  ]),

  // 字段6: 紧急程度
  紧急程度: findValue(parsed, [
    "紧急程度", "urgency", "优先级",
    "AI分析字段.紧急程度"
  ]),

  // 字段7: 主题/类别
  "主题/类别": findValue(parsed, [
    "主题/类别", "主题类别", "topic_category", "类别", "主题",
    "AI分析字段.主题类别", "AI分析字段.主题/类别"
  ]),

  // 字段8: 商业机会
  商业机会: findValue(parsed, [
    "商业机会", "business_opportunity", "机会",
    "AI分析字段.商业机会"
  ]),

  // 字段9: 转化潜力
  转化潜力: findValue(parsed, [
    "转化潜力", "conversion_potential", "潜力",
    "AI分析字段.转化潜力"
  ]),

  // 字段10: seo关键词
  seo关键词: findValue(parsed, [
    "seo关键词", "seo_keywords", "关键词", "keywords",
    "AI分析字段.seo关键词"
  ]),

  // 字段11: 中文总结
  中文总结: findValue(parsed, [
    "中文总结", "chinese_summary", "总结", "summary",
    "AI分析字段.中文总结"
  ]),

  // 字段12: linkedin创意
  linkedin创意: findValue(parsed, [
    "linkedin创意", "linkedin_creative", "linkedin",
    "社交媒体创意输出字段.linkedin创意"
  ]),

  // 字段13: twitter创意
  twitter创意: findValue(parsed, [
    "twitter创意", "twitter_creative", "twitter",
    "社交媒体创意输出字段.twitter创意"
  ]),

  // 字段14: facebook创意
  facebook创意: findValue(parsed, [
    "facebook创意", "facebook_creative", "facebook",
    "社交媒体创意输出字段.facebook创意"
  ]),

  // 字段15: instagram创意
  instagram创意: findValue(parsed, [
    "instagram创意", "instagram_creative", "instagram",
    "社交媒体创意输出字段.instagram创意"
  ]),

  // 字段16: tiktok创意
  tiktok创意: findValue(parsed, [
    "tiktok创意", "tiktok_creative", "tiktok",
    "社交媒体创意输出字段.tiktok创意"
  ]),

  // 字段17: youtube标题
  youtube标题: findValue(parsed, [
    "youtube标题", "youtube_title", "youtube",
    "社交媒体创意输出字段.youtube标题"
  ]),

  // 字段18: blog标题
  blog标题: findValue(parsed, [
    "blog标题", "blog_title", "blog",
    "社交媒体创意输出字段.blog标题"
  ])
};

// --- 8. 日志输出（调试用） ---
console.log(`✅ 行${row_number}: AI解析完成`);
console.log(`   情绪分析: ${output.情绪分析 ? '有' : '无'}`);
console.log(`   痛点: ${output.痛点 ? '有' : '无'}`);
console.log(`   用户需求: ${output.用户需求 ? '有' : '无'}`);

// --- 9. 返回标准化输出 ---
return { json: output };
