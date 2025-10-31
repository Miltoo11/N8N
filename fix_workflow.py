#!/usr/bin/env python3
"""
修复工作流：添加Merge节点并修复连接
"""

import json
import uuid

def create_merge_node(name, position):
    """创建标准Merge节点"""
    return {
        "parameters": {
            "mode": "combine",
            "combinationMode": "multiplex"
        },
        "id": str(uuid.uuid4()),
        "name": name,
        "type": "n8n-nodes-base.merge",
        "position": position,
        "typeVersion": 3
    }

def fix_workflow():
    # 读取原始工作流
    with open('Reddit监控工作流 - 增量式更新 - 评论解析附带.json', 'r', encoding='utf-8') as f:
        workflow = json.load(f)

    nodes = workflow['nodes']
    connections = workflow['connections']

    # 创建节点名称到节点的映射
    node_map = {node['name']: node for node in nodes}

    print("🔧 开始修复工作流...")

    # ============================================
    # 修复1: 在"调用Reddit API (post)"后添加Merge节点
    # ============================================
    print("\n1️⃣ 添加Merge节点：合并Reddit Post数据")

    merge_post_node = create_merge_node(
        "合并Reddit Post数据",
        [768, 192]  # 在"调用Reddit API (post)"和"提取Reddit数据 (post)"之间
    )
    nodes.append(merge_post_node)

    # 修改连接：
    # 旧: 构建Reddit URL → 调用Reddit API → 提取Reddit数据
    # 新: 构建Reddit URL ──┐
    #                    ├→ Merge → 提取Reddit数据
    #    调用Reddit API ──┘

    # 1.1 构建Reddit URL现在应该连接到两个地方：调用API + Merge(input 0)
    if "构建Reddit搜索URL (post)" in connections:
        connections["构建Reddit搜索URL (post)"]["main"] = [[
            {"node": "调用Reddit API (post)", "type": "main", "index": 0},
            {"node": "合并Reddit Post数据", "type": "main", "index": 0}
        ]]

    # 1.2 调用Reddit API现在连接到Merge(input 1)
    if "调用Reddit API (post)" in connections:
        connections["调用Reddit API (post)"]["main"] = [[
            {"node": "合并Reddit Post数据", "type": "main", "index": 1}
        ]]

    # 1.3 Merge连接到提取数据
    connections["合并Reddit Post数据"] = {
        "main": [[{"node": "提取Reddit数据 (post)", "type": "main", "index": 0}]]
    }

    # ============================================
    # 修复2: 修改"提取Reddit数据 (post)"代码，从Merge读取
    # ============================================
    print("2️⃣ 简化提取Reddit数据节点代码")

    node_map["提取Reddit数据 (post)"]["parameters"]["jsCode"] = '''// === 提取Reddit Post数据（从Merge输出读取） ===
const mergedData = $json;

// 从Merge的Input 0获取上游数据（包含row_number等）
const rowNumber = mergedData.row_number || mergedData['关键词'] ? 2 : 0;
const keyword = mergedData['关键词'] || mergedData.关键词 || '';
const subreddit = mergedData['频道'] || mergedData.频道 || '';

// 从Merge的Input 1获取Reddit API响应
const apiResponse = mergedData;
const posts = Array.isArray(apiResponse?.data?.children) ? apiResponse.data.children : [];

if (!posts.length) {
  console.log(`⚠️ 行${rowNumber}: 未找到帖子`);
  return {
    json: {
      row_number: rowNumber,
      关键词: keyword,
      频道: subreddit,
      状态: '无Reddit数据'
    }
  };
}

// 取第一个帖子
const post = posts[0]?.data || {};

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
    comment_url_api: commentsApi,
    状态: '已获取Post数据'
  }
};
'''

    # ============================================
    # 修复3: 在"调用Reddit API (comments)"后添加Merge节点
    # ============================================
    print("3️⃣ 添加Merge节点：合并Reddit Comments数据")

    merge_comments_node = create_merge_node(
        "合并Reddit Comments数据",
        [1424, 192]  # 在"调用Reddit API (comments)"和"提取Reddit数据 (comments)"之间
    )
    nodes.append(merge_comments_node)

    # 修改连接：
    # 旧: 读取更新后数据 → 调用Comments API → 提取Comments数据
    # 新: 读取更新后数据 ──┐
    #                    ├→ Merge → 提取Comments数据
    #    调用Comments API ─┘

    # 3.1 读取更新后数据连接到两个地方
    if "读取更新 (post) 后数据" in connections:
        connections["读取更新 (post) 后数据"]["main"] = [[
            {"node": "调用Reddit API (comments)", "type": "main", "index": 0},
            {"node": "合并Reddit Comments数据", "type": "main", "index": 0},
            {"node": "准备AI分析数据", "type": "main", "index": 0}
        ]]

    # 3.2 调用Comments API连接到Merge
    if "调用Reddit API (comments)" in connections:
        connections["调用Reddit API (comments)"]["main"] = [[
            {"node": "合并Reddit Comments数据", "type": "main", "index": 1}
        ]]

    # 3.3 Merge连接到提取数据
    connections["合并Reddit Comments数据"] = {
        "main": [[{"node": "提取Reddit数据 (comments)", "type": "main", "index": 0}]]
    }

    # ============================================
    # 修复4: 修改"提取Reddit数据 (comments)"代码
    # ============================================
    print("4️⃣ 简化提取Comments数据节点代码")

    node_map["提取Reddit数据 (comments)"]["parameters"]["jsCode"] = '''// === 提取Reddit Comments数据（从Merge输出读取） ===
const mergedData = $json;

// 从Merge Input 0获取上游数据
const rowNumber = mergedData.row_number || 0;
const postId = mergedData.post_id || '';

// 从Merge Input 1获取Comments API响应
let commentsApiResponse = mergedData;

// 初始化评论变量
let commentsText = '';
let commentsJSON = [];
let commentCount = 0;
let avgScore = 0;

try {
  // Reddit评论API返回数组：[帖子, 评论列表]
  if (Array.isArray(commentsApiResponse) && commentsApiResponse.length > 1) {
    const commentListing = commentsApiResponse[1]?.data?.children || [];

    const validComments = commentListing
      .filter(c => c.kind === 't1' && c.data)
      .slice(0, 10);

    commentCount = validComments.length;

    validComments.forEach((comment, index) => {
      const c = comment.data;
      const author = c.author || '[deleted]';
      const body = (c.body || '').substring(0, 200);
      const score = c.score || 0;
      const created = c.created_utc ? new Date(c.created_utc * 1000).toISOString().split('T')[0] : '';

      commentsText += `${index + 1}. @${author} (${score}👍 ${created}):\\n${body}\\n\\n`;

      commentsJSON.push({
        rank: index + 1,
        author,
        body,
        score,
        created_date: created,
        comment_id: c.id || ''
      });
    });

    if (commentCount > 0) {
      const totalScore = commentsJSON.reduce((sum, c) => sum + c.score, 0);
      avgScore = Math.round(totalScore / commentCount);
    }

    console.log(`✅ 行${rowNumber}: 成功抓取 ${commentCount} 条热评`);
  } else {
    console.log(`⚠️ 行${rowNumber}: 没有找到评论数据`);
  }
} catch (error) {
  console.log(`❌ 行${rowNumber}: 评论处理失败 - ${error.message}`);
}

return {
  json: {
    row_number: rowNumber,
    post_id: postId,
    评论: commentsText || '暂无评论',
    评论数量: commentCount,
    评论平均分: avgScore,
    状态: '已获取Comments数据'
  }
};
'''

    # ============================================
    # 修复5: 连接"更新评论数据"到AI分析流程
    # ============================================
    print("5️⃣ 修复数据流：连接评论更新到AI分析")

    # 评论更新后应该读取最终数据，但这里已经有"读取更新后数据"连接到"准备AI分析"
    # 所以我们需要确保有一个新的Read节点，或者重用现有的
    # 但为了简化，我们让"更新评论数据"连接到"准备AI分析"

    # 实际上，更合理的流程是：
    # 更新Comments → 读取最终完整数据 → 准备AI分析

    # 由于"读取更新 (post) 后数据"已经在同时触发Comments和AI分析
    # 我们需要改为：更新Comments → 读取完整数据 → AI分析

    # 添加一个新的Read节点
    read_final_node = {
        "parameters": {
            "documentId": {
                "__rl": True,
                "value": "1FKtICtmHMvlBaP8oeF_nk9LeCL28JZ2lqmWHfIHDYaw",
                "mode": "list",
                "cachedResultName": "Reddit × Gemini × Google Sheets"
            },
            "sheetName": {
                "__rl": True,
                "value": 8228757,
                "mode": "list",
                "cachedResultName": "Reddit Logistics Monitor （POST分析）"
            },
            "filtersUI": {
                "values": [
                    {
                        "lookupColumn": "row_number",
                        "lookupValue": "={{ $json.row_number }}"
                    }
                ]
            },
            "options": {}
        },
        "id": str(uuid.uuid4()),
        "name": "读取完整数据（含Comments）",
        "type": "n8n-nodes-base.googleSheets",
        "position": [1648, 192],
        "typeVersion": 4.7,
        "credentials": {
            "googleSheetsOAuth2Api": {
                "id": "GUtZ6Mnx8dlEYNgu",
                "name": "Google Sheets account"
            }
        }
    }
    nodes.append(read_final_node)

    # 更新连接
    connections["更新Reddit数据到 (comments)"] = {
        "main": [[{"node": "读取完整数据（含Comments）", "type": "main", "index": 0}]]
    }

    connections["读取完整数据（含Comments）"] = {
        "main": [[{"node": "准备AI分析数据", "type": "main", "index": 0}]]
    }

    # 移除"读取更新 (post) 后数据"到"准备AI分析"的直接连接
    # 改为只触发Comments API
    connections["读取更新 (post) 后数据"]["main"] = [[
        {"node": "调用Reddit API (comments)", "type": "main", "index": 0},
        {"node": "合并Reddit Comments数据", "type": "main", "index": 0}
    ]]

    # ============================================
    # 修复6: 在Gemini AI后添加Merge节点
    # ============================================
    print("6️⃣ 添加Merge节点：合并Gemini AI响应")

    merge_ai_node = create_merge_node(
        "合并Gemini AI响应",
        [2208, 96]
    )
    nodes.append(merge_ai_node)

    # 修改连接
    # 准备AI数据连接到两个地方
    if "准备AI分析数据" in connections:
        connections["准备AI分析数据"]["main"] = [[
            {"node": "Gemini AI分析", "type": "main", "index": 0},
            {"node": "合并Gemini AI响应", "type": "main", "index": 0}
        ]]

    # Gemini连接到Merge
    if "Gemini AI分析" in connections:
        connections["Gemini AI分析"]["main"] = [[
            {"node": "合并Gemini AI响应", "type": "main", "index": 1}
        ]]

    # Merge连接到解析
    connections["合并Gemini AI响应"] = {
        "main": [[{"node": "解析AI分析结果", "type": "main", "index": 0}]]
    }

    # ============================================
    # 修复7: 简化"解析AI分析结果"代码
    # ============================================
    print("7️⃣ 简化解析AI结果节点代码")

    # 保留原有的复杂解析逻辑，但确保从Merge读取row_number
    original_code = node_map["解析AI分析结果"]["parameters"]["jsCode"]

    # 只修改row_number获取部分
    new_code = original_code.replace(
        """const row_number =
  $json.row_number ||
  $item(0).$node["准备AI分析数据"]?.json?.row_number ||
  null;""",
        """const row_number = $json.row_number || null;"""
    )

    node_map["解析AI分析结果"]["parameters"]["jsCode"] = new_code

    # ============================================
    # 保存修复后的工作流
    # ============================================
    workflow['nodes'] = nodes
    workflow['connections'] = connections
    workflow['name'] = "Reddit监控工作流 - 增量式更新 - 修复版"

    output_file = "Reddit监控工作流 - 增量式更新 - 修复版.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(workflow, f, ensure_ascii=False, indent=2)

    print(f"\n✅ 修复完成！")
    print(f"   输出文件: {output_file}")
    print(f"   总节点数: {len(nodes)} (新增 {len(nodes) - len(workflow['nodes']) + 3})")
    print(f"   连接数: {len(connections)}")

    print("\n📋 修复摘要:")
    print("   1. 添加'合并Reddit Post数据' Merge节点")
    print("   2. 添加'合并Reddit Comments数据' Merge节点")
    print("   3. 添加'合并Gemini AI响应' Merge节点")
    print("   4. 添加'读取完整数据（含Comments）' Read节点")
    print("   5. 简化所有Code节点，从Merge读取数据")
    print("   6. 修复数据流连接，确保串行处理")

    print("\n🎯 修复后的数据流:")
    print("   Append初始数据")
    print("     ↓")
    print("   读取已写入数据")
    print("     ↓")
    print("   构建URL ──┐")
    print("            ├→ Merge → 提取Post数据 → 更新Post数据")
    print("   Reddit API┘                               ↓")
    print("                                    读取更新后数据")
    print("                                              ↓")
    print("                              ┌───────────────┘")
    print("                              ↓")
    print("                     Comments API ─┐")
    print("                                  ├→ Merge → 提取Comments → 更新Comments")
    print("                     (上游数据) ──┘                              ↓")
    print("                                                    读取完整数据（含Comments）")
    print("                                                                ↓")
    print("                                                        准备AI数据 ─┐")
    print("                                                                  ├→ Merge → 解析 → 更新AI")
    print("                                                        Gemini AI ─┘")

if __name__ == "__main__":
    fix_workflow()
