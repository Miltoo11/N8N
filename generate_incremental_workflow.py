#!/usr/bin/env python3
"""
生成增量式更新Google Sheets的n8n工作流
架构：每个阶段都更新一次表格，使用row_number和post_id追踪
"""

import json
import uuid

# Google Sheets 配置
SHEET_DOC_ID = "1FKtICtmHMvlBaP8oeF_nk9LeCL28JZ2lqmWHfIHDYaw"
SHEET_NAME = "Reddit Logistics Monitor （POST分析）"
SHEET_ID = 8228757
KEYWORDS_SHEET_ID = 997707066
SUBREDDITS_SHEET_ID = 808343003

# 凭证ID
GOOGLE_SHEETS_CRED_ID = "GUtZ6Mnx8dlEYNgu"
REDDIT_OAUTH_CRED_ID = "425YTcnxD6M8uXNU"
GEMINI_CRED_ID = "zXZHicj3I5k25blp"

def create_node(name, node_type, position, parameters=None, **kwargs):
    """创建节点"""
    node = {
        "parameters": parameters or {},
        "id": str(uuid.uuid4()),
        "name": name,
        "type": node_type,
        "position": position
    }
    node.update(kwargs)
    return node

def create_workflow():
    """创建增量式更新工作流"""

    nodes = []

    # ========================================================
    # 第一阶段：读取基础数据并写入Sheets
    # ========================================================

    # 1. 手动触发
    nodes.append(create_node(
        "手动触发",
        "n8n-nodes-base.manualTrigger",
        [-1600, 400],
        typeVersion=1
    ))

    # 2. 读取关键词表
    nodes.append(create_node(
        "读取关键词表",
        "n8n-nodes-base.googleSheets",
        [-1400, 300],
        {
            "documentId": {
                "__rl": True,
                "value": SHEET_DOC_ID,
                "mode": "list",
                "cachedResultName": "Reddit × Gemini × Google Sheets"
            },
            "sheetName": {
                "__rl": True,
                "value": KEYWORDS_SHEET_ID,
                "mode": "list",
                "cachedResultName": "key words"
            },
            "options": {}
        },
        typeVersion=4.7,
        credentials={"googleSheetsOAuth2Api": {"id": GOOGLE_SHEETS_CRED_ID, "name": "Google Sheets account"}}
    ))

    # 3. 读取频道表
    nodes.append(create_node(
        "读取频道表",
        "n8n-nodes-base.googleSheets",
        [-1400, 500],
        {
            "documentId": {
                "__rl": True,
                "value": SHEET_DOC_ID,
                "mode": "list",
                "cachedResultName": "Reddit × Gemini × Google Sheets"
            },
            "sheetName": {
                "__rl": True,
                "value": SUBREDDITS_SHEET_ID,
                "mode": "list",
                "cachedResultName": "subreddits"
            },
            "options": {}
        },
        typeVersion=4.7,
        credentials={"googleSheetsOAuth2Api": {"id": GOOGLE_SHEETS_CRED_ID, "name": "Google Sheets account"}}
    ))

    # 4. 合并数据
    nodes.append(create_node(
        "合并关键词和频道",
        "n8n-nodes-base.merge",
        [-1200, 400],
        {},
        typeVersion=3
    ))

    # 5. 交叉匹配引擎（生成关键词×频道组合）
    cross_match_code = '''// ========================================================
// 交叉匹配引擎 + row_number生成
// 功能：生成关键词×频道组合，分配row_number
// ========================================================

const MAX_COMBINATIONS = 2;
const items = $input.all();

if (!items || items.length === 0) {
  throw new Error('⚠️ 没有输入数据');
}

const keywordItems = [];
const subredditItems = [];

for (const item of items) {
  const row = item.json || {};
  if (row.Keyword || row.keyword) {
    keywordItems.push(item);
  } else if (row['频道名称'] || row.subreddit || row.name) {
    subredditItems.push(item);
  }
}

if (keywordItems.length === 0 || subredditItems.length === 0) {
  throw new Error(`❌ 数据不足 - 关键词: ${keywordItems.length}, 频道: ${subredditItems.length}`);
}

console.log(`📥 关键词: ${keywordItems.length}, 频道: ${subredditItems.length}`);

// 解析关键词
const keywords = [];
for (const item of keywordItems) {
  const row = item.json || {};
  const rawKeyword = row.Keyword || row.keyword || '';
  const priority = row['优先级'] || row.priority || '中';
  const category = row['类别'] || row.category || '';

  if (!rawKeyword.trim()) continue;

  const kwList = rawKeyword.split('|').map(k => k.trim()).filter(Boolean);
  for (const kw of kwList) {
    keywords.push({ keyword: kw, priority, category });
  }
}

// 解析频道
const subreddits = [];
for (const item of subredditItems) {
  const row = item.json || {};
  const name = row['频道名称'] || row.subreddit || row.name || '';
  const priority = row['优先级'] || row.priority || 'C';
  const members = row['成员数'] || row.members || '0';
  const classification = row['分类'] || row.classification || '';

  if (!name.trim()) continue;

  const cleanName = name.replace(/^r\\//, '').trim().replace(/\\s+/g, '');
  subreddits.push({ subreddit: cleanName, priority, members, classification });
}

console.log(`✅ 关键词: ${keywords.length}, 频道: ${subreddits.length}`);

// 生成组合 + row_number
const combinations = [];
let rowNumber = 2; // 从第2行开始（第1行是表头）

for (const kw of keywords) {
  for (const sr of subreddits) {
    if (combinations.length >= MAX_COMBINATIONS) break;

    combinations.push({
      row_number: rowNumber++,
      关键词: kw.keyword,
      keyword_priority: kw.priority,
      keyword_category: kw.category,
      频道: sr.subreddit,
      subreddit_priority: sr.priority,
      subreddit_members: sr.members,
      subreddit_classification: sr.classification,
      平台: 'Reddit',
      行业: kw.category || sr.classification,
      post_id: '',  // 初始为空，Reddit阶段填充
      链接: '',     // 初始为空
      状态: '待处理'
    });
  }
  if (combinations.length >= MAX_COMBINATIONS) break;
}

console.log(`✅ 生成 ${combinations.length} 个组合`);
return combinations.map(c => ({ json: c }));
'''

    nodes.append(create_node(
        "交叉匹配引擎",
        "n8n-nodes-base.code",
        [-1000, 400],
        {"jsCode": cross_match_code},
        typeVersion=2
    ))

    # 6. 第一次写入Sheets（Append基础数据）
    nodes.append(create_node(
        "Append初始数据到Sheets",
        "n8n-nodes-base.googleSheets",
        [-800, 400],
        {
            "operation": "append",
            "documentId": {
                "__rl": True,
                "value": SHEET_DOC_ID,
                "mode": "list",
                "cachedResultName": "Reddit × Gemini × Google Sheets"
            },
            "sheetName": {
                "__rl": True,
                "value": SHEET_ID,
                "mode": "list",
                "cachedResultName": SHEET_NAME
            },
            "columns": {
                "mappingMode": "defineBelow",
                "value": {
                    "row_number": "={{ $json.row_number }}",
                    "关键词": "={{ $json.关键词 }}",
                    "频道": "={{ $json.频道 }}",
                    "行业": "={{ $json.行业 }}",
                    "平台": "={{ $json.平台 }}",
                    "post_id": "={{ $json.post_id }}",
                    "链接": "={{ $json.链接 }}",
                    "状态": "={{ $json.状态 }}"
                }
            },
            "options": {}
        },
        typeVersion=4.7,
        credentials={"googleSheetsOAuth2Api": {"id": GOOGLE_SHEETS_CRED_ID, "name": "Google Sheets account"}}
    ))

    # ========================================================
    # 第二阶段：Reddit数据获取并更新Sheets
    # ========================================================

    # 7. Read Sheets（读取刚写入的数据）
    nodes.append(create_node(
        "读取已写入数据",
        "n8n-nodes-base.googleSheets",
        [-600, 400],
        {
            "documentId": {
                "__rl": True,
                "value": SHEET_DOC_ID,
                "mode": "list",
                "cachedResultName": "Reddit × Gemini × Google Sheets"
            },
            "sheetName": {
                "__rl": True,
                "value": SHEET_ID,
                "mode": "list",
                "cachedResultName": SHEET_NAME
            },
            "options": {
                "range": "A2:Z1000"  # 从第2行开始读取
            }
        },
        typeVersion=4.7,
        credentials={"googleSheetsOAuth2Api": {"id": GOOGLE_SHEETS_CRED_ID, "name": "Google Sheets account"}}
    ))

    # 8. 构建Reddit搜索URL
    build_url_code = '''// 构建Reddit搜索URL
const item = $input.item;
const data = item.json || {};

const keyword = data['关键词'] || data.keyword || '';
const subreddit = data['频道'] || data.subreddit || '';
const rowNumber = data['row_number'] || 0;

if (!keyword || !subreddit) {
  console.log('❌ 缺少关键词或频道');
  return [];
}

const searchUrl = `https://oauth.reddit.com/r/${subreddit}/search` +
  `?q=${encodeURIComponent(keyword)}` +
  `&restrict_sr=1&sort=new&limit=1&t=week&include_over_18=1&raw_json=1`;

return {
  json: {
    ...data,
    row_number: rowNumber,
    search_url: searchUrl
  }
};
'''

    nodes.append(create_node(
        "构建Reddit搜索URL",
        "n8n-nodes-base.code",
        [-400, 400],
        {"jsCode": build_url_code},
        typeVersion=2
    ))

    # 9. 调用Reddit API
    nodes.append(create_node(
        "调用Reddit API",
        "n8n-nodes-base.httpRequest",
        [-200, 400],
        {
            "url": "={{ $json.search_url }}",
            "authentication": "genericCredentialType",
            "genericAuthType": "oAuth2Api",
            "sendHeaders": True,
            "headerParameters": {
                "parameters": [
                    {"name": "User-Agent", "value": "n8n-workflow/2.0(u/Repulsive_Mark_7919)"},
                    {"name": "Accept", "value": "application/json"}
                ]
            },
            "options": {
                "timeout": 30000,
                "batching": {
                    "batch": {
                        "batchSize": 1,
                        "batchInterval": 2000
                    }
                }
            }
        },
        typeVersion=4.2,
        retryOnFail=True,
        maxTries=3,
        waitBetweenTries=2000,
        alwaysOutputData=True,
        credentials={"oAuth2Api": {"id": REDDIT_OAUTH_CRED_ID, "name": "n8n rR API"}}
    ))

    # 10. 合并Reddit响应
    nodes.append(create_node(
        "合并Reddit数据",
        "n8n-nodes-base.merge",
        [0, 400],
        {
            "mode": "combine",
            "combinationMode": "multiplex"
        },
        typeVersion=3
    ))

    # 11. 提取Reddit数据
    extract_reddit_code = '''// 提取Reddit帖子数据并保留row_number
const item = $input.item;
const mergedData = item.json || {};

const rowNumber = mergedData.row_number || 0;
const keyword = mergedData['关键词'] || mergedData.keyword || '';
const subreddit = mergedData['频道'] || mergedData.subreddit || '';

// 提取API响应
const apiData = mergedData.data || mergedData;
const posts = Array.isArray(apiData.children) ? apiData.children : [];

if (!posts.length) {
  console.log(`⚠️ 行${rowNumber}: 未找到帖子`);
  return {
    json: {
      row_number: rowNumber,
      关键词: keyword,
      频道: subreddit,
      状态: '无数据'
    }
  };
}

// 取第一个帖子
const post = posts[0].data || {};

const title = (post.title || '').substring(0, 500);
const selftext = (post.selftext || '').substring(0, 20000);
const score = Number(post.score) || 0;
const numComments = Number(post.num_comments) || 0;
const upvoteRatio = Number(post.upvote_ratio) || 0;
const postId = post.id || '';
const permalink = post.permalink ? 'https://reddit.com' + post.permalink : '';
const author = post.author || '';
const createdUtc = Number(post.created_utc) || 0;
const postDate = createdUtc ? new Date(createdUtc * 1000).toISOString().split('T')[0] : '';

const commentsApi = postId ? `https://oauth.reddit.com/comments/${postId}.json?limit=50&depth=1&sort=top&raw_json=1` : '';

console.log(`✅ 行${rowNumber}: 提取帖子 ${postId}`);

return {
  json: {
    row_number: rowNumber,
    关键词: keyword,
    频道: subreddit,
    post_id: postId,
    标题: title,
    原文: selftext,
    作者: author,
    score: score,
    upvote_ratio: upvoteRatio,
    评论数: numComments,
    链接: permalink,
    post发布日期: postDate,
    comments_api_url: commentsApi,
    状态: '已获取Reddit数据'
  }
};
'''

    nodes.append(create_node(
        "提取Reddit数据",
        "n8n-nodes-base.code",
        [200, 400],
        {"jsCode": extract_reddit_code},
        typeVersion=2,
        alwaysOutputData=True
    ))

    # 12. Update Sheets（Reddit数据）
    nodes.append(create_node(
        "更新Reddit数据到Sheets",
        "n8n-nodes-base.googleSheets",
        [400, 400],
        {
            "operation": "update",
            "documentId": {
                "__rl": True,
                "value": SHEET_DOC_ID,
                "mode": "list",
                "cachedResultName": "Reddit × Gemini × Google Sheets"
            },
            "sheetName": {
                "__rl": True,
                "value": SHEET_ID,
                "mode": "list",
                "cachedResultName": SHEET_NAME
            },
            "columns": {
                "mappingMode": "defineBelow",
                "value": {
                    "post_id": "={{ $json.post_id }}",
                    "标题": "={{ $json.标题 }}",
                    "原文": "={{ $json.原文 }}",
                    "作者": "={{ $json.作者 }}",
                    "score": "={{ $json.score }}",
                    "upvote_ratio": "={{ $json.upvote_ratio }}",
                    "评论数": "={{ $json.评论数 }}",
                    "链接": "={{ $json.链接 }}",
                    "post发布日期": "={{ $json.post发布日期 }}",
                    "comments_api_url": "={{ $json.comments_api_url }}",
                    "状态": "={{ $json.状态 }}"
                },
                "matchingColumns": ["row_number"]
            },
            "options": {}
        },
        typeVersion=4.7,
        credentials={"googleSheetsOAuth2Api": {"id": GOOGLE_SHEETS_CRED_ID, "name": "Google Sheets account"}}
    ))

    # ========================================================
    # 第三阶段：AI分析并更新Sheets
    # ========================================================

    # 13. Get Sheets（读取更新后的数据）
    nodes.append(create_node(
        "读取更新后数据",
        "n8n-nodes-base.googleSheets",
        [600, 400],
        {
            "documentId": {
                "__rl": True,
                "value": SHEET_DOC_ID,
                "mode": "list",
                "cachedResultName": "Reddit × Gemini × Google Sheets"
            },
            "sheetName": {
                "__rl": True,
                "value": SHEET_ID,
                "mode": "list",
                "cachedResultName": SHEET_NAME
            },
            "options": {
                "range": "A2:Z1000"
            }
        },
        typeVersion=4.7,
        credentials={"googleSheetsOAuth2Api": {"id": GOOGLE_SHEETS_CRED_ID, "name": "Google Sheets account"}}
    ))

    # 14. 准备AI分析数据
    prepare_ai_code = '''// 准备AI分析数据并保留row_number
const item = $input.item;
const data = item.json || {};

const rowNumber = data.row_number || 0;
const postId = data.post_id || '';
const title = data['标题'] || '';
const selftext = data['原文'] || '';

// 只分析有内容的帖子
if (!postId || (!title && !selftext)) {
  console.log(`⚠️ 行${rowNumber}: 无内容，跳过AI分析`);
  return [];
}

console.log(`📤 行${rowNumber}: 准备AI分析`);

return {
  json: {
    row_number: rowNumber,
    post_id: postId,
    title: title,
    selftext: selftext,
    keyword: data['关键词'] || '',
    subreddit: data['频道'] || ''
  }
};
'''

    nodes.append(create_node(
        "准备AI分析数据",
        "n8n-nodes-base.code",
        [800, 400],
        {"jsCode": prepare_ai_code},
        typeVersion=2
    ))

    # 15. Gemini API分析
    gemini_body = {
        "contents": [{
            "role": "user",
            "parts": [{
                "text": "You are an expert in logistics, e-commerce, and social media marketing. Analyze the provided Reddit post and return a JSON object with your analysis.\\n\\n**Post Data:**\\nTitle: {{ $json.title }}\\nContent: {{ $json.selftext }}\\n\\n**Required JSON Output:**\\n{\\n  \\\"sentiment\\\": \\\"string (Positive/Neutral/Negative)\\\",\\n  \\\"sentiment_score\\\": \\\"integer (0-100)\\\",\\n  \\\"pain_points\\\": \\\"string\\\",\\n  \\\"user_needs\\\": \\\"string\\\",\\n  \\\"urgency\\\": \\\"string (High/Medium/Low)\\\",\\n  \\\"topic_category\\\": \\\"string\\\",\\n  \\\"conversion_potential\\\": \\\"string (High/Medium/Low)\\\",\\n  \\\"chinese_summary\\\": \\\"string\\\"\\n}"
            }]
        }],
        "generationConfig": {
            "temperature": 0.35,
            "responseMimeType": "application/json"
        }
    }

    nodes.append(create_node(
        "Gemini AI分析",
        "n8n-nodes-base.httpRequest",
        [1000, 400],
        {
            "method": "POST",
            "url": "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent",
            "authentication": "predefinedCredentialType",
            "nodeCredentialType": "googlePalmApi",
            "sendHeaders": True,
            "headerParameters": {
                "parameters": [
                    {"name": "Content-Type", "value": "application/json"}
                ]
            },
            "sendBody": True,
            "specifyBody": "json",
            "jsonBody": "={{ " + json.dumps(gemini_body) + " }}",
            "options": {
                "batching": {
                    "batch": {
                        "batchSize": 1,
                        "batchInterval": 3000
                    }
                },
                "response": {
                    "response": {
                        "responseFormat": "json"
                    }
                },
                "timeout": 60000
            }
        },
        typeVersion=4.2,
        retryOnFail=True,
        maxTries=2,
        waitBetweenTries=5000,
        alwaysOutputData=True,
        credentials={"googlePalmApi": {"id": GEMINI_CRED_ID, "name": "Google Gemini(PaLM) Api account"}}
    ))

    # 16. 合并AI结果
    nodes.append(create_node(
        "合并AI分析结果",
        "n8n-nodes-base.merge",
        [1200, 400],
        {
            "mode": "combine",
            "combinationMode": "multiplex"
        },
        typeVersion=3
    ))

    # 17. 解析AI结果
    parse_ai_code = '''// 解析AI分析结果并保留row_number
const item = $input.item;
const mergedData = item.json || {};

const rowNumber = mergedData.row_number || 0;
const postId = mergedData.post_id || '';

// 默认AI结果
let aiData = {
  情绪分析: '未分析',
  情绪分析分数: 0,
  痛点: '',
  用户需求: '',
  紧急程度: '低',
  主题类别: '',
  转化潜力: '低',
  中文总结: ''
};

// 解析Gemini响应
try {
  if (mergedData.candidates && Array.isArray(mergedData.candidates)) {
    const candidate = mergedData.candidates[0];
    if (candidate?.content?.parts?.[0]?.text) {
      const text = candidate.content.parts[0].text;
      const cleanText = text.replace(/```json\\s*|```\\s*/g, '').trim();
      const jsonMatch = cleanText.match(/\\{[\\s\\S]*\\}/);

      if (jsonMatch) {
        const parsed = JSON.parse(jsonMatch[0]);
        aiData = {
          情绪分析: parsed.sentiment || '未分析',
          情绪分析分数: parsed.sentiment_score || 0,
          痛点: parsed.pain_points || '',
          用户需求: parsed.user_needs || '',
          紧急程度: parsed.urgency || '低',
          主题类别: parsed.topic_category || '',
          转化潜力: parsed.conversion_potential || '低',
          中文总结: parsed.chinese_summary || ''
        };
        console.log(`✅ 行${rowNumber}: AI分析完成`);
      }
    }
  }
} catch (error) {
  console.log(`❌ 行${rowNumber}: AI解析失败 - ${error.message}`);
}

return {
  json: {
    row_number: rowNumber,
    post_id: postId,
    ...aiData,
    状态: 'AI分析完成'
  }
};
'''

    nodes.append(create_node(
        "解析AI分析结果",
        "n8n-nodes-base.code",
        [1400, 400],
        {"jsCode": parse_ai_code},
        typeVersion=2
    ))

    # 18. Update Sheets（AI数据）
    nodes.append(create_node(
        "更新AI分析到Sheets",
        "n8n-nodes-base.googleSheets",
        [1600, 400],
        {
            "operation": "update",
            "documentId": {
                "__rl": True,
                "value": SHEET_DOC_ID,
                "mode": "list",
                "cachedResultName": "Reddit × Gemini × Google Sheets"
            },
            "sheetName": {
                "__rl": True,
                "value": SHEET_ID,
                "mode": "list",
                "cachedResultName": SHEET_NAME
            },
            "columns": {
                "mappingMode": "defineBelow",
                "value": {
                    "情绪分析": "={{ $json.情绪分析 }}",
                    "情绪分析分数": "={{ $json.情绪分析分数 }}",
                    "痛点": "={{ $json.痛点 }}",
                    "用户需求": "={{ $json.用户需求 }}",
                    "紧急程度": "={{ $json.紧急程度 }}",
                    "主题/类别": "={{ $json.主题类别 }}",
                    "转化潜力": "={{ $json.转化潜力 }}",
                    "中文总结": "={{ $json.中文总结 }}",
                    "状态": "={{ $json.状态 }}"
                },
                "matchingColumns": ["row_number"]
            },
            "options": {}
        },
        typeVersion=4.7,
        credentials={"googleSheetsOAuth2Api": {"id": GOOGLE_SHEETS_CRED_ID, "name": "Google Sheets account"}}
    ))

    # ========================================================
    # 构建连接关系
    # ========================================================

    connections = {
        "手动触发": {
            "main": [[
                {"node": "读取关键词表", "type": "main", "index": 0},
                {"node": "读取频道表", "type": "main", "index": 0}
            ]]
        },
        "读取关键词表": {
            "main": [[{"node": "合并关键词和频道", "type": "main", "index": 0}]]
        },
        "读取频道表": {
            "main": [[{"node": "合并关键词和频道", "type": "main", "index": 1}]]
        },
        "合并关键词和频道": {
            "main": [[{"node": "交叉匹配引擎", "type": "main", "index": 0}]]
        },
        "交叉匹配引擎": {
            "main": [[{"node": "Append初始数据到Sheets", "type": "main", "index": 0}]]
        },
        "Append初始数据到Sheets": {
            "main": [[{"node": "读取已写入数据", "type": "main", "index": 0}]]
        },
        "读取已写入数据": {
            "main": [[
                {"node": "构建Reddit搜索URL", "type": "main", "index": 0}
            ]]
        },
        "构建Reddit搜索URL": {
            "main": [[
                {"node": "调用Reddit API", "type": "main", "index": 0},
                {"node": "合并Reddit数据", "type": "main", "index": 0}
            ]]
        },
        "调用Reddit API": {
            "main": [[{"node": "合并Reddit数据", "type": "main", "index": 1}]]
        },
        "合并Reddit数据": {
            "main": [[{"node": "提取Reddit数据", "type": "main", "index": 0}]]
        },
        "提取Reddit数据": {
            "main": [[{"node": "更新Reddit数据到Sheets", "type": "main", "index": 0}]]
        },
        "更新Reddit数据到Sheets": {
            "main": [[{"node": "读取更新后数据", "type": "main", "index": 0}]]
        },
        "读取更新后数据": {
            "main": [[
                {"node": "准备AI分析数据", "type": "main", "index": 0}
            ]]
        },
        "准备AI分析数据": {
            "main": [[
                {"node": "Gemini AI分析", "type": "main", "index": 0},
                {"node": "合并AI分析结果", "type": "main", "index": 0}
            ]]
        },
        "Gemini AI分析": {
            "main": [[{"node": "合并AI分析结果", "type": "main", "index": 1}]]
        },
        "合并AI分析结果": {
            "main": [[{"node": "解析AI分析结果", "type": "main", "index": 0}]]
        },
        "解析AI分析结果": {
            "main": [[{"node": "更新AI分析到Sheets", "type": "main", "index": 0}]]
        }
    }

    # 构建完整工作流
    workflow = {
        "name": "Reddit监控工作流 - 增量式更新",
        "nodes": nodes,
        "pinData": {},
        "connections": connections,
        "active": False,
        "settings": {
            "executionOrder": "v1"
        },
        "versionId": str(uuid.uuid4()),
        "meta": {
            "templateCredsSetupCompleted": True,
            "instanceId": "cf3a3e94a3582062b1bbb0314be4475a417462d0865c5094dcc2ad7edb7d7989"
        },
        "id": "incremental-workflow-" + str(uuid.uuid4())[:8],
        "tags": []
    }

    return workflow

if __name__ == "__main__":
    workflow = create_workflow()
    output_file = "Reddit监控工作流 - 增量式更新.json"

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(workflow, f, ensure_ascii=False, indent=2)

    print(f"✅ 工作流已生成: {output_file}")
    print(f"   节点数: {len(workflow['nodes'])}")
    print(f"   连接数: {len(workflow['connections'])}")
    print()
    print("架构说明：")
    print("阶段1: 关键词×频道 → Append到Sheets（写入row_number、基础信息）")
    print("阶段2: Read Sheets → Reddit API → Update Sheets（更新Reddit数据）")
    print("阶段3: Get Sheets → Gemini API → Update Sheets（更新AI分析）")
    print()
    print("关键特性：")
    print("- 每个阶段都更新一次表格")
    print("- 使用row_number追踪每一行")
    print("- 使用post_id标识帖子")
    print("- Update操作基于row_number匹配")
