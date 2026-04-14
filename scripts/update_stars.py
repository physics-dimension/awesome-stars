#!/usr/bin/env python3
"""
Fetch GitHub starred repos and generate categorized README files (Chinese + English).
Uses curated_data.json as primary data source, with keyword-based fallback for new stars.
"""

import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from collections import defaultdict

# ---------------------------------------------------------------------------
# MECE Category Definitions (order matters for display)
# ---------------------------------------------------------------------------
CATEGORIES = [
    {"id": "agent-frameworks", "name_zh": "AI Agent 框架与编排", "name_en": "AI Agent Frameworks & Orchestration",
     "desc_zh": "构建、运行、编排智能体的平台、SDK 与多 Agent 系统",
     "desc_en": "Core agent platforms, SDKs, multi-agent systems and orchestration runtimes",
     "keywords": ["agent-framework", "multi-agent", "agent-sdk", "harness", "agentic-framework", "swarm", "orchestration", "superagent", "langgraph"]},
    {"id": "agent-skills", "name_zh": "Agent Skills 与插件", "name_en": "Agent Skills & Plugins",
     "desc_zh": "技能合集、单项技能、技能市场与管理工具",
     "desc_en": "Skill collections, individual skills, skill managers and marketplaces",
     "keywords": ["agent-skills", "skills", "skill", "claude-skills", "openclaw-skills", "codex-skills", "skill-collection", "skill-manager"]},
    {"id": "claude-ecosystem", "name_zh": "Claude / OpenClaw 生态", "name_en": "Claude / OpenClaw Ecosystem",
     "desc_zh": "围绕 Claude 产品线的客户端、扩展、配置、教程与学习资源",
     "desc_en": "Clients, extensions, configurations, tutorials and learning resources for the Claude product line",
     "keywords": ["claude-code", "claude", "openclaw", "claudecode", "droid", "clawdbot"]},
    {"id": "memory-context", "name_zh": "AI 记忆与上下文", "name_en": "AI Memory & Context",
     "desc_zh": "记忆系统、上下文数据库、长期记忆管理",
     "desc_en": "Memory systems, context databases, and long-term memory management",
     "keywords": ["memory", "agent-memory", "context-engineering", "long-term-memory", "context-database"]},
    {"id": "research-search", "name_zh": "研究与深度搜索", "name_en": "Research & Deep Search",
     "desc_zh": "自主研究 Agent、深度搜索、网络信息抓取与聚合",
     "desc_en": "Autonomous research agents, deep search, web scraping and information aggregation",
     "keywords": ["deep-research", "research-agent", "web-scraper", "search", "autonomous-research"]},
    {"id": "dev-infra", "name_zh": "开发工具与基础设施", "name_en": "Dev Tools & Infrastructure",
     "desc_zh": "Spec 驱动开发、MCP 工具、浏览器自动化、CLI 与 DevTools",
     "desc_en": "Spec-driven development, MCP tools, browser automation, CLIs, and DevTools",
     "keywords": ["spec-driven", "mcp-server", "mcp", "devtools", "browser-automation", "cli", "workflow-automation"]},
    {"id": "ui-design", "name_zh": "UI/UX 与前端", "name_en": "UI/UX & Frontend",
     "desc_zh": "前端组件库、设计系统、SaaS 模板与设计工具",
     "desc_en": "Frontend component libraries, design systems, SaaS templates, and design tools",
     "keywords": ["component-library", "design-system", "ui", "shadcn", "tailwindcss", "react-components", "saas-boilerplate"]},
    {"id": "content-media", "name_zh": "内容创作与媒体", "name_en": "Content Creation & Media",
     "desc_zh": "视频/图片生成、社交媒体发布、文档转换与创意工具",
     "desc_en": "Video/image generation, social media publishing, document conversion, and creative tools",
     "keywords": ["video", "social-media", "content", "screen-recorder", "poster", "wechat", "markdown"]},
    {"id": "api-proxy", "name_zh": "API 代理与模型接入", "name_en": "API Proxy & Model Access",
     "desc_zh": "模型 API 逆向、订阅转发、Token 管理与 CLI 代理",
     "desc_en": "Model API proxies, reverse-engineered APIs, subscription relay, and CLI proxies",
     "keywords": ["2api", "reverse-engineering", "proxy", "free-api"]},
    {"id": "productivity-knowledge", "name_zh": "效率、知识与通讯", "name_en": "Productivity, Knowledge & Communication",
     "desc_zh": "笔记工具、第二大脑、监控仪表盘与个人 AI 助手",
     "desc_en": "Note-taking, second brain, monitoring dashboards, and personal AI assistants",
     "keywords": ["obsidian", "note-taking", "productivity", "knowledge", "monitoring", "dashboard"]},
    {"id": "communication-chat", "name_zh": "通讯平台与聊天机器人", "name_en": "Communication & Chatbots",
     "desc_zh": "IM 平台集成、聊天机器人、语音工具与社交自动化",
     "desc_en": "IM platform integrations, chatbots, voice tools, and social automation",
     "keywords": ["chatbot", "telegram", "discord", "qq", "im"]},
    {"id": "llm-research", "name_zh": "LLM 研究与学术", "name_en": "LLM Research & Academia",
     "desc_zh": "LLM 评测、提示词工程、社会模拟、预测系统与学术资源",
     "desc_en": "LLM evaluation, prompt engineering, social simulation, prediction, and academic resources",
     "keywords": ["llm", "prompt-engineering", "evaluation", "evals", "simulation", "prediction", "dspy"]},
]

CAT_INDEX = {c["id"]: c for c in CATEGORIES}


def fetch_starred_repos(username):
    """Fetch all starred repos via gh CLI."""
    repos = []
    page = 1
    while True:
        result = subprocess.run(
            ["gh", "api", "users/{}/starred?per_page=100&page={}".format(username, page),
             "-H", "Accept: application/vnd.github.v3+json"],
            capture_output=True, text=True, encoding="utf-8", errors="replace"
        )
        if result.returncode != 0:
            print("Error fetching page {}: {}".format(page, result.stderr), file=sys.stderr)
            break
        page_repos = json.loads(result.stdout)
        if not page_repos:
            break
        repos.extend(page_repos)
        if len(page_repos) < 100:
            break
        page += 1
    return repos


def auto_classify(repo):
    """Fallback: keyword-based classification for repos not in curated data."""
    topics = set(repo.get("topics") or [])
    desc = (repo.get("description") or "").lower()
    name_lower = repo["full_name"].lower()

    scores = defaultdict(int)
    for cat in CATEGORIES:
        for kw in cat["keywords"]:
            kw_lower = kw.lower()
            if kw_lower in topics:
                scores[cat["id"]] += 3
            if kw_lower in desc:
                scores[cat["id"]] += 2
            if kw_lower in name_lower:
                scores[cat["id"]] += 1

    if scores:
        best = max(scores, key=scores.get)
        if scores[best] > 0:
            return best
    return "dev-infra"  # safe default


def format_stars(count):
    if count >= 1000:
        return "{:.1f}k".format(count / 1000)
    return str(count)


def generate_readme(repos, lang, username, curated, previous_repos=None):
    """Generate categorized README content."""
    classified = defaultdict(list)
    for repo in repos:
        full_name = repo["full_name"]
        if full_name in curated:
            cat_id = curated[full_name]["category"]
        else:
            cat_id = auto_classify(repo)
        classified[cat_id].append(repo)

    for cat_id in classified:
        classified[cat_id].sort(key=lambda r: r.get("stargazers_count", 0), reverse=True)

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    total = len(repos)
    current_repos = set(r["full_name"] for r in repos)
    new_repos = current_repos - previous_repos if previous_repos else set()

    is_zh = lang == "zh"
    lines = []

    # Header
    lines.append("# Awesome Stars")
    lines.append("")
    if is_zh:
        lines.append("> 我的 GitHub Star 索引 | 按 MECE 原则分类整理 | 每周一自动更新")
        lines.append(">")
        lines.append("> **[@{}](https://github.com/{})**  的 Star 收藏夹".format(username, username))
    else:
        lines.append("> My GitHub Stars index | MECE-categorized | Auto-updated weekly on Mondays")
        lines.append(">")
        lines.append("> **[@{}](https://github.com/{})**'s Star Collection".format(username, username))
    lines.append("")
    lines.append("[![Update Stars](https://github.com/{}/awesome-stars/actions/workflows/update-stars.yml/badge.svg)](https://github.com/{}/awesome-stars/actions/workflows/update-stars.yml)".format(username, username))
    lines.append("")

    if is_zh:
        lines.append("**最近更新**: {} | **总计**: {} 个仓库".format(now, total))
    else:
        lines.append("**Last Updated**: {} | **Total**: {} repos".format(now, total))
    lines.append("")

    if new_repos:
        if is_zh:
            lines.append("**本周新增**: {} 个仓库".format(len(new_repos)))
        else:
            lines.append("**New this week**: {} repos".format(len(new_repos)))
        lines.append("")

    # TOC
    if is_zh:
        lines.append("## 目录")
    else:
        lines.append("## Table of Contents")
    lines.append("")
    for cat in CATEGORIES:
        count = len(classified.get(cat["id"], []))
        if count > 0:
            name = cat["name_zh"] if is_zh else cat["name_en"]
            lines.append("- [{name}](#{id}) ({count})".format(name=name, id=cat["id"], count=count))
    lines.append("")

    # Content
    for cat in CATEGORIES:
        cat_repos = classified.get(cat["id"], [])
        if not cat_repos:
            continue

        cat_name = cat["name_zh"] if is_zh else cat["name_en"]
        cat_desc = cat["desc_zh"] if is_zh else cat["desc_en"]

        lines.append("## {}".format(cat_name))
        lines.append('<a id="{}"></a>'.format(cat["id"]))
        lines.append("")
        lines.append("*{}*".format(cat_desc))
        lines.append("")

        if is_zh:
            lines.append("| 仓库 | 描述 | 语言 | Stars |")
        else:
            lines.append("| Repository | Description | Language | Stars |")
        lines.append("| --- | --- | --- | --- |")

        for r in cat_repos:
            full_name = r["full_name"]
            url = r["html_url"]
            lang_tag = r.get("language") or "-"
            stars = format_stars(r.get("stargazers_count", 0))
            new_badge = " **NEW**" if full_name in new_repos else ""

            if is_zh:
                # Use curated Chinese desc, fallback to original
                if full_name in curated and curated[full_name].get("desc_zh"):
                    desc = curated[full_name]["desc_zh"]
                else:
                    desc = (r.get("description") or "暂无描述")[:100]
            else:
                desc = (r.get("description") or "No description")[:200]

            desc = desc.replace("|", "\\|").replace("\n", " ")
            lines.append("| [{}]({}){} | {} | `{}` | {} |".format(full_name, url, new_badge, desc, lang_tag, stars))
        lines.append("")

    # Footer
    lines.append("---")
    lines.append("")
    if is_zh:
        lines.append("*本索引由 [GitHub Actions](.github/workflows/update-stars.yml) 自动生成，每周一更新*")
        lines.append("")
        lines.append("[English Version](README_EN.md)")
    else:
        lines.append("*This index is auto-generated by [GitHub Actions](.github/workflows/update-stars.yml), updated every Monday*")
        lines.append("")
        lines.append("[中文版](README.md)")

    return "\n".join(lines)


def main():
    # Get username
    result = subprocess.run(
        ["gh", "api", "user", "--jq", ".login"],
        capture_output=True, text=True, encoding="utf-8", errors="replace"
    )
    if result.returncode != 0:
        username = os.environ.get("GITHUB_USERNAME", "")
        if not username and len(sys.argv) > 1:
            username = sys.argv[1]
        if not username:
            print("Error: Could not determine GitHub username", file=sys.stderr)
            sys.exit(1)
    else:
        username = result.stdout.strip()

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    # Load curated data
    curated_path = os.path.join(base_dir, "curated_data.json")
    curated = {}
    if os.path.exists(curated_path):
        with open(curated_path, "r", encoding="utf-8") as f:
            curated = json.load(f)
        print("Loaded {} curated entries".format(len(curated)))
    else:
        print("Warning: curated_data.json not found, using auto-classification only", file=sys.stderr)

    print("Fetching starred repos for @{}...".format(username))
    repos = fetch_starred_repos(username)
    print("Found {} starred repos".format(len(repos)))

    if not repos:
        print("No starred repos found!", file=sys.stderr)
        sys.exit(1)

    # Load previous state for diff
    state_file = os.path.join(base_dir, ".repo_state.json")
    previous_repos = None
    if os.path.exists(state_file):
        with open(state_file, "r", encoding="utf-8") as f:
            previous_repos = set(json.load(f))

    # Find uncurated repos
    current_names = set(r["full_name"] for r in repos)
    uncurated = current_names - set(curated.keys())
    if uncurated:
        print("\n{} repos not in curated_data.json (auto-classified):".format(len(uncurated)))
        for name in sorted(uncurated):
            print("  - {}".format(name))

    # Generate READMEs
    readme_zh = generate_readme(repos, "zh", username, curated, previous_repos)
    with open(os.path.join(base_dir, "README.md"), "w", encoding="utf-8") as f:
        f.write(readme_zh)
    print("\nGenerated README.md (Chinese)")

    readme_en = generate_readme(repos, "en", username, curated, previous_repos)
    with open(os.path.join(base_dir, "README_EN.md"), "w", encoding="utf-8") as f:
        f.write(readme_en)
    print("Generated README_EN.md (English)")

    # Save state
    names = [r["full_name"] for r in repos]
    with open(state_file, "w", encoding="utf-8") as f:
        json.dump(names, f, indent=2)

    # Print summary
    classified_counts = defaultdict(int)
    for repo in repos:
        full_name = repo["full_name"]
        if full_name in curated:
            cat_id = curated[full_name]["category"]
        else:
            cat_id = auto_classify(repo)
        classified_counts[cat_id] += 1

    print("\n--- Category Summary ---")
    for cat in CATEGORIES:
        count = classified_counts.get(cat["id"], 0)
        if count > 0:
            print("  {}: {}".format(cat["name_zh"], count))


if __name__ == "__main__":
    main()
