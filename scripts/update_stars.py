#!/usr/bin/env python3
"""
Fetch GitHub starred repos and generate categorized README files (Chinese + English).
Uses MECE (Mutually Exclusive, Collectively Exhaustive) categorization.
"""

import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from collections import defaultdict

# ---------------------------------------------------------------------------
# MECE Category Definitions
# ---------------------------------------------------------------------------
CATEGORIES = [
    {
        "id": "agent-frameworks",
        "name_zh": "AI Agent 框架与编排",
        "name_en": "AI Agent Frameworks & Orchestration",
        "desc_zh": "核心智能体平台、多智能体系统、Agent SDK 与运行时",
        "desc_en": "Core agent platforms, multi-agent systems, Agent SDKs and runtimes",
        "keywords": [
            "agent-framework", "multi-agent", "agent-sdk", "harness",
            "agentic-framework", "swarm", "orchestration", "agent harness",
            "superagent", "langgraph", "langchain", "crew",
        ],
        "repo_patterns": [
            "openclaw/openclaw", "NousResearch/hermes-agent", "bytedance/deer-flow",
            "FoundationAgents/MetaGPT", "FlowiseAI/Flowise", "EvoAgentX/EvoAgentX",
            "HKUDS/ClawTeam", "MiniMax-AI/Mini-Agent", "shareAI-lab/Kode-Agent",
            "shareAI-lab/kode-agent-sdk", "codeany-ai/open-agent-sdk-typescript",
            "uluckyXH/OpenMOSS", "Yeachan-Heo/oh-my-claudecode",
            "code-yeongyu/oh-my-openagent", "mindfold-ai/Trellis",
            "obra/superpowers", "Memento-Teams/Memento-Skills",
            "shareAI-lab/learn-claude", "danielmiessler/Fabric",
            "ChesterRa/cccc", "HKUDS/CLI-Anything",
            "msitarzewski/agency-agents", "tanweai/pua", "puaclaw/PUAClaw",
        ],
    },
    {
        "id": "agent-skills",
        "name_zh": "Agent Skills 与插件生态",
        "name_en": "Agent Skills & Plugin Ecosystem",
        "desc_zh": "技能合集、单项技能、技能管理工具与市场",
        "desc_en": "Skill collections, individual skills, skill managers and marketplaces",
        "keywords": [
            "agent-skills", "skills", "skill", "claude-skills",
            "openclaw-skills", "codex-skills", "skill-collection",
            "skill-manager", "marketplace",
        ],
        "repo_patterns": [
            "addyosmani/agent-skills", "VoltAgent/awesome-agent-skills",
            "VoltAgent/awesome-droid-subagents", "VoltAgent/awesome-openclaw-skills",
            "anthropics/skills", "phuryn/pm-skills", "mattpocock/skills",
            "KKKKhazix/khazix-skills", "zephyrwang6/pm-skills",
            "MiniMax-AI/skills", "remotion-dev/skills", "vercel-labs/agent-skills",
            "LeoYeAI/openclaw-master-skills", "JimLiu/baoyu-skills",
            "github/awesome-copilot", "ComposioHQ/awesome-claude-skills",
            "BehiSecc/awesome-claude-skills", "GuDaStudio/skills",
            "jeremylongshore/claude-plugins-plus-skills",
            "yusufkaraaslan/Skill_Seekers", "Backtthefuture/skillmanager",
            "buzhangsan/skill-manager", "K-Dense-AI/scientific-agent-skills",
            "aahl/skills", "shareAI-lab/shareAI-skills",
            "sukilll/great-product-skills", "yaojingang/yao-meta-skill",
            "lijigang/ljg-skills", "GuDaStudio/commands",
            "wuhongchen/content-collector-skill",
            "lst97/claude-sub-agents",
        ],
    },
    {
        "id": "claude-ecosystem",
        "name_zh": "Claude / OpenClaw 工具链",
        "name_en": "Claude / OpenClaw Toolchain",
        "desc_zh": "围绕 Claude 和 OpenClaw 的扩展、客户端、配置与学习资源",
        "desc_en": "Extensions, clients, configurations and learning resources for Claude and OpenClaw",
        "keywords": [
            "claude-plugin", "droid-extension", "droid",
            "claude-config", "claudecode",
        ],
        "repo_patterns": [
            "factory-ai/droid", "droid-best/claude",
            "wuxiran/cc-pane", "hellowind777/hello2cc",
            "Haleclipse/CCometixLine", "Haleclipse/Claudix", "Haleclipse/Claudex",
            "farion1231/cc-switch", "slopus/happy", "tiann/hapi",
            "andrepimenta/droid-chat", "musistudio/droid-router",
            "777genius/claude_agent_teams_ui", "DevAgentForge/Open-Claude-Cowork",
            "different-ai/openwork", "iOfficeAI/AionUi", "SumeLabs/clawra",
            "op7418/CodePilot", "DeadWaveWave/opencove",
            "ikook-wang/cc-sync", "frankbria/ralph-claude",
            "breaking-brake/cc-wf-studio", "diet103/droid-infrastructure-showcase",
            "davila7/droid-templates", "ykdojo/droid-tips",
            "lintsinghua/droid-book", "affaan-m/everything-droid",
            "garrytan/gstack", "garrytan/gbrain",
            "drona23/claude-token-efficient",
            "hesamsheikh/awesome-openclaw-usecases",
            "yeuxuan/openclaw-docs", "NoeFabris/droid-antigravity-auth",
            "BloopAI/vibe-kanban", "thedotmack/claude-mem",
            "workany-ai/workany", "PeonPing/peon-ping",
            "wusimpl/AntigravityQuotaWatcher",
        ],
    },
    {
        "id": "memory-context",
        "name_zh": "AI 记忆与上下文工程",
        "name_en": "AI Memory & Context Engineering",
        "desc_zh": "记忆系统、上下文数据库、长期记忆管理",
        "desc_en": "Memory systems, context databases, and long-term memory management",
        "keywords": [
            "memory", "agent-memory", "context-engineering",
            "long-term-memory", "context-database",
        ],
        "repo_patterns": [
            "mem0ai/mem0", "MemPalace/mempalace", "Goldentrii/AgentRecall",
            "EverMind-AI/EverOS", "NevaMind-AI/memU",
            "volcengine/OpenViking", "volcengine/MineContext",
            "gnekt/My-Brain-Is-Full-Crew",
        ],
    },
    {
        "id": "research-search",
        "name_zh": "深度研究与信息获取",
        "name_en": "Deep Research & Information Retrieval",
        "desc_zh": "自主研究 Agent、深度搜索、网络信息抓取与聚合",
        "desc_en": "Autonomous research agents, deep search, web scraping and information aggregation",
        "keywords": [
            "deep-research", "research", "search", "web-scraper",
            "autonomous-research", "research-agent",
        ],
        "repo_patterns": [
            "karpathy/autoresearch", "aiming-lab/AutoResearchClaw",
            "assafelovic/gpt-researcher", "MiroMindAI/MiroThinker",
            "Panniantong/Agent-Reach", "eze-is/web-access",
            "GuDaStudio/GrokSearch", "joeseesun/qiaomu-markdown-proxy",
            "blessonism/openclaw-search-skills", "blessonism/github-explorer-skill",
            "astonysh/OpenClaw-DeepReeder", "zarazhangrui/follow-builders",
            "epiral/bb-browser", "steel-dev/awesome-web-agents",
        ],
    },
    {
        "id": "ui-design",
        "name_zh": "UI/UX 设计与组件库",
        "name_en": "UI/UX Design & Component Libraries",
        "desc_zh": "前端组件库、设计系统、设计工具与 SaaS 模板",
        "desc_en": "Frontend component libraries, design systems, design tools, and SaaS templates",
        "keywords": [
            "component-library", "design-system", "ui", "shadcn",
            "tailwindcss", "react-components", "design",
            "saas-boilerplate", "saas-starter", "boilerplate",
        ],
        "repo_patterns": [
            "shadcn-ui/ui", "mui/material-ui", "heroui-inc/heroui",
            "magicuidesign/magicui", "unovue/shadcn-vue", "jnsahaj/tweakcn",
            "hunvreus/basecoat", "Ali-Hussein-dev/indie-ui",
            "origin-space/ui-experiments", "VoltAgent/awesome-design-md",
            "pbakaus/impeccable", "benjitaylor/agentation",
            "GalaxyXieyu/Design-Learn", "refscn/rplibs",
            "nextlevelbuilder/ui-ux-pro-max-skill",
            "nextjs/saas-starter", "ixartz/SaaS-Boilerplate",
            "wasp-lang/open-saas",
            "jau123/MeiGen-AI-Design-MCP",
        ],
    },
    {
        "id": "content-media",
        "name_zh": "内容创作与多媒体",
        "name_en": "Content Creation & Multimedia",
        "desc_zh": "视频生成、社交媒体自动化、文档转换、创意工具",
        "desc_en": "Video generation, social media automation, document conversion, and creative tools",
        "keywords": [
            "video", "social-media", "content", "markdown",
            "screen-recorder", "poster", "wechat",
        ],
        "repo_patterns": [
            "remotion-dev/remotion", "webadderall/Recordly",
            "saturndec/waoowaoo", "dreammis/social-auto-upload",
            "doocs/md", "microsoft/markitdown",
            "geekjourneyx/md2wechat-skill", "oaker-io/wewrite",
            "op7418/Document-illustrator-skill",
            "joeseesun/qiaomu-mondo-poster-design",
            "liangdabiao/Seedance2-Storyboard-Generator",
            "ZeroLu/awesome-seedance",
            "Vimalinx-zero/OpenClaw-Newspaper",
            "op7418/Humanizer-zh", "funstory-ai/BabelDOC",
            "AmElmo/proofshot",
        ],
    },
    {
        "id": "api-proxy",
        "name_zh": "API 代理与逆向工程",
        "name_en": "API Proxy & Reverse Engineering",
        "desc_zh": "模型 API 代理、逆向工程 API、订阅转发服务",
        "desc_en": "Model API proxies, reverse-engineered APIs, subscription relay services",
        "keywords": [
            "2api", "reverse-engineering", "proxy", "api",
            "free-api", "freeapi",
        ],
        "repo_patterns": [
            "bohesocool/you2api", "chenyme/grok2api",
            "TheSmallHanCat/sora2api", "TheSmallHanCat/flow2api",
            "TheSmallHanCat/Flow2API-Token-Updater",
            "caiwuu/web2api", "lanqian528/chat2api",
            "CJackHwang/ds2api", "YuJunZhiXue/qwen2API",
            "iptag/jimeng-api", "wwwzhouhui/jimeng-free-api-all",
            "HanaokaYuzu/Gemini-API", "lulistart/Kiro2api-Node",
            "hank9999/kiro.rs",
            "Wei-Shaw/sub2api", "router-for-me/CLIProxyAPI",
            "rtk-ai/rtk",
        ],
    },
    {
        "id": "productivity-knowledge",
        "name_zh": "效率工具与知识管理",
        "name_en": "Productivity & Knowledge Management",
        "desc_zh": "笔记工具、第二大脑、监控仪表盘、个人 AI 助手",
        "desc_en": "Note-taking, second brain, monitoring dashboards, and personal AI assistants",
        "keywords": [
            "obsidian", "note-taking", "productivity", "knowledge",
            "second-brain", "monitoring", "dashboard",
        ],
        "repo_patterns": [
            "kepano/obsidian-skills", "YishenTu/claudian",
            "heyitsnoah/claudesidian", "obsidian-tasks-group/obsidian-tasks",
            "axtonliu/axton-obsidian-visual-skills",
            "SamSongAI/Trace", "usememos/memos",
            "khoj-ai/khoj", "mindverse/Second-Me",
            "koala73/worldmonitor", "wm94i/Work_Review",
            "danielmiessler/Personal_AI_Infrastructure",
            "WishMelz/imgurl", "PehZeroV/tidyflux",
            "blueberrycongee/termcanvas", "chapterv/Tapnow-Studio-PP",
        ],
    },
    {
        "id": "dev-infra",
        "name_zh": "开发工具与基础设施",
        "name_en": "Development Tools & Infrastructure",
        "desc_zh": "Spec 驱动开发、MCP 工具、浏览器自动化、CLI 与 DevTools",
        "desc_en": "Spec-driven development, MCP tools, browser automation, CLIs, and DevTools",
        "keywords": [
            "spec-driven", "mcp-server", "mcp", "devtools",
            "browser-automation", "cli",
        ],
        "repo_patterns": [
            "github/spec-kit", "Fission-AI/OpenSpec", "yibie/SPEC-AGENTS.md",
            "gsd-build/get-shit-done", "gsd-build/gsd-2",
            "ChromeDevTools/chrome-devtools-mcp",
            "mcp-router/mcp-router", "hustcc/mcp-mermaid",
            "lgazo/drawio-mcp-server", "yctimlin/mcp_excalidraw",
            "qy527145/acemcp", "GuDaStudio/codexmcp",
            "czlonkowski/n8n-mcp",
            "larksuite/cli", "DayuanJiang/next-ai-draw-io",
            "liujuntao123/smart-excalidraw-next",
            "vibesurf-ai/VibeSurf",
            "codecrafters-io/build-your-own-x",
            "Done-0/value-realization",
        ],
    },
    {
        "id": "llm-research",
        "name_zh": "LLM 工程与 AI 研究",
        "name_en": "LLM Engineering & AI Research",
        "desc_zh": "LLM 评测、提示词工程、社会模拟、预测系统与学术资源",
        "desc_en": "LLM evaluation, prompt engineering, social simulation, prediction, and academic resources",
        "keywords": [
            "llm", "prompt-engineering", "evaluation", "evals",
            "simulation", "prediction", "dspy",
        ],
        "repo_patterns": [
            "openai/evals", "f/prompts.chat", "stanfordnlp/dspy",
            "karpathy/llm-council", "weitianxin/Awesome-Agentic-Reasoning",
            "tsinghua-fib-lab/AgentSociety", "joonspk-research/generative_agents",
            "camel-ai/oasis", "666ghj/MiroFish", "666ghj/BettaFish",
            "adongwanai/AgentGuide",
            "OpenBB-finance/OpenBB", "anthropics/financial-services-plugins",
        ],
    },
    {
        "id": "communication-chat",
        "name_zh": "通讯平台与聊天机器人",
        "name_en": "Communication Platforms & Chatbots",
        "desc_zh": "IM 平台集成、聊天机器人、语音工具与社交自动化",
        "desc_en": "IM platform integrations, chatbots, voice tools, and social automation",
        "keywords": [
            "chatbot", "telegram", "discord", "wechat", "qq",
            "im", "chat",
        ],
        "repo_patterns": [
            "AstrBotDevs/AstrBot", "Mai-with-u/MaiBot",
            "op7418/Claude-to-IM-skill", "woniu9524/ParallelChat",
            "rikkahub/rikkahub", "freestylefly/wechat-cli",
            "teng-lin/notebooklm-py", "yan5xu/ququ",
            "oyxning/astrbot_plugin_antipromptinjector",
            "KeloYuan/Niki-AI",
        ],
    },
    {
        "id": "creative-misc",
        "name_zh": "思维蒸馏与其他",
        "name_en": "Thought Distillation & Miscellaneous",
        "desc_zh": "将个人思维蒸馏为 AI 技能的创意项目，以及其他未分类工具",
        "desc_en": "Creative projects that distill personal thinking into AI skills, and other uncategorized tools",
        "keywords": [],
        "repo_patterns": [
            "alchaincyf/nuwa-skill", "therealXiaomanChu/ex-skill",
            "titanwings/colleague-skill", "FANzR-arch/Numerologist_skills",
            "tw93/Waza", "lijigang/ljg-skill-xray-article",
            "lijigang/ljg-skill-xray-paper", "lijigang/ljg-skill-xray-book",
            "santifer/career-ops", "hua1995116/indiehackers-steps",
            "Zie619/n8n-workflows",
            "DiningFactory/panda-vpn-pro",
            "huangyunbin/resource",
            "mileson/agent-onboarding",
            "LeoLB-Wang/wukong-invite-helper",
        ],
    },
]


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


def classify_repo(repo):
    """Assign a repo to a MECE category. Returns category id."""
    full_name = repo["full_name"]
    topics = set(repo.get("topics") or [])
    desc = (repo.get("description") or "").lower()
    name_lower = full_name.lower()

    # 1. Check explicit repo patterns first (highest priority)
    for cat in CATEGORIES:
        if full_name in cat["repo_patterns"]:
            return cat["id"]

    # 2. Check keywords against topics and description
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

    # 3. Fallback
    return "creative-misc"


def format_stars(count):
    """Format star count with K suffix for readability."""
    if count >= 1000:
        return "{:.1f}k".format(count / 1000)
    return str(count)


def generate_readme(repos, lang, username, previous_repos=None):
    """Generate categorized README content."""
    # Classify all repos
    classified = defaultdict(list)
    for repo in repos:
        cat_id = classify_repo(repo)
        classified[cat_id].append(repo)

    # Sort each category by stars (descending)
    for cat_id in classified:
        classified[cat_id].sort(key=lambda r: r.get("stargazers_count", 0), reverse=True)

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    total = len(repos)

    # Detect new repos
    current_repos = set(r["full_name"] for r in repos)
    new_repos = current_repos - previous_repos if previous_repos else set()

    if lang == "zh":
        lines = [
            "# Awesome Stars",
            "",
            "> 我的 GitHub Star 索引 | 按 MECE 原则分类整理 | 每周一自动更新",
            ">",
            "> **[@{}](https://github.com/{})**  的 Star 收藏夹".format(username, username),
            "",
            "[![Update Stars](https://github.com/{}/awesome-stars/actions/workflows/update-stars.yml/badge.svg)](https://github.com/{}/awesome-stars/actions/workflows/update-stars.yml)".format(username, username),
            "",
            "**最近更新**: {} | **总计**: {} 个仓库".format(now, total),
            "",
        ]
        if new_repos:
            lines.append("**本周新增**: {} 个仓库".format(len(new_repos)))
            lines.append("")

        # Table of contents
        lines.append("## 目录")
        lines.append("")
        for cat in CATEGORIES:
            count = len(classified.get(cat["id"], []))
            if count > 0:
                lines.append("- [{name}](#{id}) ({count})".format(name=cat["name_zh"], id=cat["id"], count=count))
        lines.append("")

        # Content
        for cat in CATEGORIES:
            cat_repos = classified.get(cat["id"], [])
            if not cat_repos:
                continue
            lines.append("## {}".format(cat["name_zh"]))
            lines.append('<a id="{}"></a>'.format(cat["id"]))
            lines.append("")
            lines.append("*{}*".format(cat["desc_zh"]))
            lines.append("")
            lines.append("| 仓库 | 描述 | 语言 | Stars |")
            lines.append("| --- | --- | --- | --- |")
            for r in cat_repos:
                name = r["full_name"]
                url = r["html_url"]
                desc = (r.get("description") or "暂无描述")[:150].replace("|", "\\|").replace("\n", " ")
                lang_tag = r.get("language") or "-"
                stars = format_stars(r.get("stargazers_count", 0))
                new_badge = " **NEW**" if name in new_repos else ""
                lines.append("| [{}]({}){} | {} | `{}` | {} |".format(name, url, new_badge, desc, lang_tag, stars))
            lines.append("")

        lines.append("---")
        lines.append("")
        lines.append("*本索引由 [GitHub Actions](.github/workflows/update-stars.yml) 自动生成，每周一更新*")
        lines.append("")
        lines.append("[English Version](README_EN.md)")
        return "\n".join(lines)
    else:
        lines = [
            "# Awesome Stars",
            "",
            "> My GitHub Stars index | MECE-categorized | Auto-updated weekly on Mondays",
            ">",
            "> **[@{}](https://github.com/{})**'s Star Collection".format(username, username),
            "",
            "[![Update Stars](https://github.com/{}/awesome-stars/actions/workflows/update-stars.yml/badge.svg)](https://github.com/{}/awesome-stars/actions/workflows/update-stars.yml)".format(username, username),
            "",
            "**Last Updated**: {} | **Total**: {} repos".format(now, total),
            "",
        ]
        if new_repos:
            lines.append("**New this week**: {} repos".format(len(new_repos)))
            lines.append("")

        # TOC
        lines.append("## Table of Contents")
        lines.append("")
        for cat in CATEGORIES:
            count = len(classified.get(cat["id"], []))
            if count > 0:
                lines.append("- [{name}](#{id}) ({count})".format(name=cat["name_en"], id=cat["id"], count=count))
        lines.append("")

        # Content
        for cat in CATEGORIES:
            cat_repos = classified.get(cat["id"], [])
            if not cat_repos:
                continue
            lines.append("## {}".format(cat["name_en"]))
            lines.append('<a id="{}"></a>'.format(cat["id"]))
            lines.append("")
            lines.append("*{}*".format(cat["desc_en"]))
            lines.append("")
            lines.append("| Repository | Description | Language | Stars |")
            lines.append("| --- | --- | --- | --- |")
            for r in cat_repos:
                name = r["full_name"]
                url = r["html_url"]
                desc = (r.get("description") or "No description")[:200].replace("|", "\\|").replace("\n", " ")
                lang_tag = r.get("language") or "-"
                stars = format_stars(r.get("stargazers_count", 0))
                new_badge = " **NEW**" if name in new_repos else ""
                lines.append("| [{}]({}){} | {} | `{}` | {} |".format(name, url, new_badge, desc, lang_tag, stars))
            lines.append("")

        lines.append("---")
        lines.append("")
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

    print("Fetching starred repos for @{}...".format(username))
    repos = fetch_starred_repos(username)
    print("Found {} starred repos".format(len(repos)))

    if not repos:
        print("No starred repos found!", file=sys.stderr)
        sys.exit(1)

    # Load previous state for diff
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    state_file = os.path.join(base_dir, ".repo_state.json")
    previous_repos = None
    if os.path.exists(state_file):
        with open(state_file, "r") as f:
            previous_repos = set(json.load(f))

    # Generate READMEs
    readme_zh = generate_readme(repos, "zh", username, previous_repos)
    with open(os.path.join(base_dir, "README.md"), "w", encoding="utf-8") as f:
        f.write(readme_zh)
    print("Generated README.md (Chinese)")

    readme_en = generate_readme(repos, "en", username, previous_repos)
    with open(os.path.join(base_dir, "README_EN.md"), "w", encoding="utf-8") as f:
        f.write(readme_en)
    print("Generated README_EN.md (English)")

    # Save state
    names = [r["full_name"] for r in repos]
    with open(state_file, "w") as f:
        json.dump(names, f, indent=2)
    print("Saved repo state for future diff")

    # Print summary
    classified_counts = defaultdict(int)
    for repo in repos:
        cat_id = classify_repo(repo)
        classified_counts[cat_id] += 1

    print("\n--- Category Summary ---")
    for cat in CATEGORIES:
        count = classified_counts.get(cat["id"], 0)
        if count > 0:
            print("  {}: {}".format(cat["name_zh"], count))

    if previous_repos:
        current = set(r["full_name"] for r in repos)
        new = current - previous_repos
        removed = previous_repos - current
        if new:
            print("\n  New stars: {}".format(len(new)))
        if removed:
            print("  Removed stars: {}".format(len(removed)))


if __name__ == "__main__":
    main()
