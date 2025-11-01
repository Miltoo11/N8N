#!/usr/bin/env python3
"""
修复Reddit工作流11.1.1的问题
问题1: 缺少Merge节点导致comment_url_api丢失
问题2: 读取节点的过滤器导致items从10减少到1
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
    with open('Reddit监控工作流11.1.1.json', 'r', encoding='utf-8') as f:
        workflow = json.load(f)

    nodes = workflow['nodes']
    connections = workflow['connections']
    node_map = {node['name']: node for node in nodes}

    print("🔧 开始修复工作流11.1.1...")
    print(f"原始节点数: {len(nodes)}")

    # ============================================
    # 修复1: 移除"读取已写入数据"的过滤器
    # ============================================
    print("\n1️⃣ 修复"读取已写入数据"节点")

    if "读取已写入数据" in node_map:
        # 移除过滤器，读取所有数据
        node_map["读取已写入数据"]["parameters"]["filtersUI"] = {}
        print("   ✅ 已移除过滤器，现在会读取所有已写入的数据")

    # ============================================
    # 修复2: 添加Merge节点 - Reddit Post
    # ============================================
    print("\n2️⃣ 添加Merge节点：合并Reddit Post数据")

    merge_post = create_merge_node("合并Reddit Post数据", [1200, 400])
    nodes.append(merge_post)

    # 修改连接
    if "构建Reddit搜索URL (post)" in connections:
        connections["构建Reddit搜索URL (post)"]["main"] = [[
            {"node": "调用Reddit API (post)", "type": "main", "index": 0},
            {"node": "合并Reddit Post数据", "type": "main", "index": 0}
        ]]

    if "调用Reddit API (post)" in connections:
        connections["调用Reddit API (post)"]["main"] = [[
            {"node": "合并Reddit Post数据", "type": "main", "index": 1}
        ]]

    connections["合并Reddit Post数据"] = {
        "main": [[{"node": "提取Reddit数据 (post)", "type": "main", "index": 0}]]
    }

    # 简化"提取Reddit数据 (post)"代码
    node_map["提取Reddit数据 (post)"]["parameters"]["jsCode"] = '''// === 提取Reddit Post数据（从Merge读取） ===
const mergedData = $json;

// 提取上游数据
const keyword = mergedData['关键词'] || mergedData.keyword || '';
const subreddit = mergedData['频道'] || mergedData.subreddit || '';

// 提取Reddit API响应
const apiData = mergedData.data || mergedData;
const posts = Array.isArray(apiData.children) ? apiData.children : [];

if (!posts.length) {
  console.log(`⚠️ 未找到帖子: ${keyword} in ${subreddit}`);
  return [];
}

const post = posts[0].data;
const title = (post.title || '').substring(0, 500);
const selftext = (post.selftext || '').substring(0, 20000);
const postId = post.id || '';
const permalink = post.permalink ? 'https://reddit.com' + post.permalink : '';
const commentsApi = postId ? `https://oauth.reddit.com/comments/${postId}.json?limit=50&depth=1&sort=top&raw_json=1` : '';

console.log(`✅ 提取帖子: ${postId}`);

return {
  json: {
    关键词: keyword,
    频道: subreddit,
    post_id: postId,
    标题: title,
    原文: selftext,
    作者: post.author || '',
    score: Number(post.score) || 0,
    upvote_ratio: Number(post.upvote_ratio) || 0,
    评论数: Number(post.num_comments) || 0,
    链接: permalink,
    post发布日期: post.created_utc ? new Date(post.created_utc * 1000).toISOString().split('T')[0] : '',
    comment_url_api: commentsApi
  }
};
'''

    # ============================================
    # 修复3: 添加Merge节点 - Reddit Comments
    # ============================================
    print("3️⃣ 添加Merge节点：合并Reddit Comments数据")

    merge_comments = create_merge_node("合并Reddit Comments数据", [1800, 400])
    nodes.append(merge_comments)

    # 修改连接
    if "读取更新 (post) 后数据" in connections:
        connections["读取更新 (post) 后数据"]["main"] = [[
            {"node": "调用Reddit API (comments)", "type": "main", "index": 0},
            {"node": "合并Reddit Comments数据", "type": "main", "index": 0}
        ]]

    if "调用Reddit API (comments)" in connections:
        connections["调用Reddit API (comments)"]["main"] = [[
            {"node": "合并Reddit Comments数据", "type": "main", "index": 1}
        ]]

    connections["合并Reddit Comments数据"] = {
        "main": [[{"node": "提取Reddit数据 (comments)", "type": "main", "index": 0}]]
    }

    # 简化"提取Reddit数据 (comments)"代码
    node_map["提取Reddit数据 (comments)"]["parameters"]["jsCode"] = '''// === 提取Reddit Comments数据（从Merge读取） ===
const mergedData = $json;

const postId = mergedData.post_id || '';
let commentsApiResponse = mergedData;

// 处理评论
let commentsText = '';
let commentCount = 0;

try {
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
      commentsText += `${index + 1}. @${author} (${score}👍):\\n${body}\\n\\n`;
    });

    console.log(`✅ 成功抓取 ${commentCount} 条评论`);
  }
} catch (error) {
  console.log(`❌ 评论处理失败: ${error.message}`);
}

return {
  json: {
    ...mergedData,  // 保留所有上游字段
    评论: commentsText || '暂无评论',
    评论数量: commentCount
  }
};
'''

    # ============================================
    # 修复4: 添加"读取完整数据"节点
    # ============================================
    print("4️⃣ 添加"读取完整数据"节点")

    read_final = {
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
            "options": {}
        },
        "id": str(uuid.uuid4()),
        "name": "读取完整数据（含Comments）",
        "type": "n8n-nodes-base.googleSheets",
        "position": [2100, 400],
        "typeVersion": 4.7,
        "credentials": {
            "googleSheetsOAuth2Api": {
                "id": "GUtZ6Mnx8dlEYNgu",
                "name": "Google Sheets account"
            }
        }
    }
    nodes.append(read_final)

    # 修改连接：Comments更新后读取完整数据
    connections["更新Reddit数据到 (comments)"] = {
        "main": [[{"node": "读取完整数据（含Comments）", "type": "main", "index": 0}]]
    }

    connections["读取完整数据（含Comments）"] = {
        "main": [[{"node": "准备AI分析数据", "type": "main", "index": 0}]]
    }

    # 移除"读取更新 (post) 后数据"到"准备AI分析数据"的直接连接
    # 只保留到Comments API的连接
    # 这个已经在修复3中处理了

    # ============================================
    # 修复5: 添加Merge节点 - Gemini AI
    # ============================================
    print("5️⃣ 添加Merge节点：合并Gemini AI响应")

    merge_ai = create_merge_node("合并Gemini AI响应", [2700, 400])
    nodes.append(merge_ai)

    # 修改连接
    if "准备AI分析数据" in connections:
        connections["准备AI分析数据"]["main"] = [[
            {"node": "Gemini AI分析", "type": "main", "index": 0},
            {"node": "合并Gemini AI响应", "type": "main", "index": 0}
        ]]

    if "Gemini AI分析" in connections:
        connections["Gemini AI分析"]["main"] = [[
            {"node": "合并Gemini AI响应", "type": "main", "index": 1}
        ]]

    connections["合并Gemini AI响应"] = {
        "main": [[{"node": "解析AI分析结果", "type": "main", "index": 0}]]
    }

    # 简化"解析AI分析结果"，使用修复版的Gemini解析器
    with open('fixed_gemini_parser.js', 'r', encoding='utf-8') as f:
        fixed_parser = f.read()

    node_map["解析AI分析结果"]["parameters"]["jsCode"] = fixed_parser

    # ============================================
    # 修复6: 修改"调用Reddit API (comments)"的URL
    # ============================================
    print("6️⃣ 修复Comments API URL")

    node_map["调用Reddit API (comments)"]["parameters"]["url"] = "={{ $json.comment_url_api }}"

    # ============================================
    # 保存修复后的工作流
    # ============================================
    workflow['nodes'] = nodes
    workflow['connections'] = connections
    workflow['name'] = "Reddit监控工作流 - 11.1.2修复版"

    output_file = "Reddit监控工作流11.1.2.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(workflow, f, ensure_ascii=False, indent=2)

    print(f"\n✅ 修复完成！")
    print(f"   输出文件: {output_file}")
    print(f"   节点数: {len(nodes)} (原{len(nodes) - 4} → 新{len(nodes)}，新增4个)")
    print(f"   连接数: {len(connections)}")

    print("\n📋 修复摘要:")
    print("   1. ✅ 移除"读取已写入数据"的过滤器 - 解决items减少问题")
    print("   2. ✅ 添加"合并Reddit Post数据" Merge节点 - 保留comment_url_api")
    print("   3. ✅ 添加"合并Reddit Comments数据" Merge节点 - 保留上游数据")
    print("   4. ✅ 添加"读取完整数据（含Comments）"节点 - 修复数据流")
    print("   5. ✅ 添加"合并Gemini AI响应" Merge节点 - 保留row_number")
    print("   6. ✅ 修复Comments API URL配置")
    print("   7. ✅ 应用修复版Gemini解析器")

    print("\n🎯 修复后的数据流:")
    print("   Append初始数据")
    print("     ↓")
    print("   读取已写入数据（全部数据，无过滤）")
    print("     ↓")
    print("   构建URL ──┐")
    print("            ├→ Merge → 提取Post → 更新Post")
    print("   Reddit API┘                        ↓")
    print("                              读取更新后数据")
    print("                                      ↓")
    print("                          Comments API ──┐")
    print("                                        ├→ Merge → 提取Comments → 更新Comments")
    print("                          (上游数据) ───┘                              ↓")
    print("                                                            读取完整数据（含Comments）")
    print("                                                                        ↓")
    print("                                                                准备AI数据 ─┐")
    print("                                                                          ├→ Merge → 解析 → 更新AI")
    print("                                                                Gemini AI ─┘")

    return workflow

if __name__ == "__main__":
    fix_workflow()
