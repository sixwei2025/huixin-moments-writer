#!/usr/bin/env python3
"""汇芯朋友圈文案规划器（moments_planner.py）

零外部依赖（纯 Python 3 标准库），支持：
1. 查看 6 大主流行业配置与合规红线；
2. 按「行业 + 文案类型 + 素材」生成结构化朋友圈创作任务单；
3. 一键生成 6 天黄金配比朋友圈排期日历（兼顾活人感、专业度与转化）。
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any

INDUSTRIES: dict[str, dict[str, Any]] = {
    "ai": {
        "name": "AI与一人公司",
        "aliases": ["ai", "AI", "一人公司", "AI与一人公司", "人工智能", "智能体"],
        "audience": "中小微企业老板、独立创业者、想用AI提效的业务负责人",
        "winning_angles": [
            "真实耗时对比（以前人工1天 vs 现在AI 10分钟）",
            "工作台实操过程与真实交付结果",
            "老板视角的用人/试错成本账",
        ],
        "pitfalls": "只聊大模型参数或泛科幻预测，容易吸引看热闹的路人而不转化客户",
        "redlines": "严禁吹嘘零门槛躺赚、一键日入过万；严禁使用硬闸/门闸等生硬工程黑话",
        "photo_tips": "工作台真实界面截图、实操前后对比图、讲课/交付现场实拍",
        "best_times": ["08:15", "12:15", "20:30"],
    },
    "tax": {
        "name": "财税企服",
        "aliases": ["tax", "财税", "财税企服", "税务", "记账", "企业服务"],
        "audience": "实体/电商/服务业老板、公司股东、个体户主理人",
        "winning_angles": [
            "公转私风险与发薪分红税差算账",
            "个体户 vs 有限公司决策对比",
            "真实客户咨询时算出来的一笔具体避险账",
        ],
        "pitfalls": "只教小会计怎么填表做分录，看似热闹实则全是同行在看，零老板转化",
        "redlines": "严禁教偷漏税、虚开、买发票或违规筹划；须写明适用税制与政策前提",
        "photo_tips": "手写算账草稿图、白板税负对比图、脱敏后的测算表局部",
        "best_times": ["08:30", "12:00", "19:30"],
    },
    "home": {
        "name": "家装本地",
        "aliases": ["home", "家装", "家装本地", "装修", "室内设计", "全屋定制"],
        "audience": "同城刚需/改善业主（正在看房、收房、准备装修的本地人群）",
        "winning_angles": [
            "工地水电/防水/收口翻车避雷实拍",
            "真实报价拆解（必须带城市+面积+半包/全包+总价范围）",
            "完工实景对比与业主真实入住反馈",
        ],
        "pitfalls": "只发网图风精修效果图、不标城市和面积预算，业主不敢问且互动极低",
        "redlines": "不恶意点名攻击同行；报价必须写明城市、面积及半包/全包范围，禁止低价钓鱼",
        "photo_tips": "工地实拍细节图、报价清单局部、完工实景前后对比",
        "best_times": ["12:15", "18:30", "21:00"],
    },
    "dental": {
        "name": "口腔医美",
        "aliases": ["dental", "口腔", "医美", "口腔医美", "牙科", "皮肤管理"],
        "audience": "怕被坑、怕疼、怕隐形消费的本地真实就诊/变美顾客",
        "winning_angles": [
            "顾客第一视角顾虑解答（疼不疼、怎么收费、值不值得做）",
            "透明就诊全流程拆解（进店→检查→方案→清单）",
            "不同材料实物对比与各自适用人群",
        ],
        "pitfalls": "大段复制教科书式干科普，或天天刷屏低价团购硬广",
        "redlines": "医疗广告硬红线：禁最/第一/根治/无痛包好；禁承诺疗效；须加注以面诊检查为准",
        "photo_tips": "诊室真实环境、材料实物对比照、手写术后注意事项",
        "best_times": ["12:00", "18:15", "20:45"],
    },
    "legal": {
        "name": "法律咨询",
        "aliases": ["legal", "法律", "法律咨询", "律所", "律师", "法务"],
        "audience": "面临纠纷的个人（婚姻/借贷/劳动）或需要合同/用工风控的企业老板",
        "winning_angles": [
            "维权取证细节（聊天记录怎么留、转账备注怎么写才有效）",
            "企业合同漏洞与用工风控（高客单常年顾问切口）",
            "把热点事件落回普通人当下能做的1个防坑动作",
        ],
        "pitfalls": "只对社会新闻做情绪输出，没把问题落回合同审查与证据留存动作",
        "redlines": "律宣红线：禁包赢/必离/保证回款；真实案情彻底脱敏；不抨击司法机关与同行",
        "photo_tips": "脱敏合同批注截图、法条重点划线图、律所开庭/工作日常",
        "best_times": ["08:30", "12:30", "21:00"],
    },
    "maternal": {
        "name": "母婴消费",
        "aliases": ["maternal", "母婴", "母婴消费", "育儿", "宝妈", "母婴店"],
        "audience": "0-6岁宝妈、准妈妈及帮带娃的家庭消费决策者",
        "winning_angles": [
            "外包装国标代码与配料表核对实拍",
            "真实空瓶清单与吃灰踩坑清单",
            "三方（妈妈+爸爸+老人）带娃与选品决策对照",
        ],
        "pitfalls": "用精致网图硬夸参数，或一味跟同行卷低价",
        "redlines": "严禁普通食品/日用品宣称治疗或医用级；国标与配料表必须真实实拍可核验",
        "photo_tips": "产品背面配料表/国标特写、真实使用空瓶照、家庭日常互动瞬间",
        "best_times": ["09:30", "13:30", "21:15"],
    },
}

POST_TYPES: dict[str, dict[str, Any]] = {
    "生活洞察": {
        "code": "life_insight",
        "goal": "展示活人感与思考深度，从日常小事自然切入行业规律",
        "length_range": "120–260 字",
        "skeleton": [
            "【生活切片】刚发生的一件具体小事（时间/人物/细节）",
            "【拐点】我当时突然想到 / 其实做我们这行也一样",
            "【行业洞察】1-2 句说透背后的商业或专业真相",
            "【轻收尾】一句平实感悟，留白给评论区接话",
        ],
        "comment_hook": "在评论区补一句自己的小吐槽或提问，拉高互动",
    },
    "实战案例": {
        "code": "case_study",
        "goal": "用真实解决过程与具体结果建立专业信任",
        "length_range": "150–300 字",
        "skeleton": [
            "【客户卡点】今天刚处理完一个客户的真实难题，一开始他以为……",
            "【拆解动作】具体查了/改了哪 2 个关键细节",
            "【真实结果】省了多少时间/避了什么坑/拿到什么结果",
            "【提醒】遇到类似情况，先做什么、别做什么",
        ],
        "comment_hook": "评论区补充一句脱敏后的小细节或避坑提示",
    },
    "反常识破局": {
        "code": "counter_intuitive",
        "goal": "打破受众常见误区，建立懂行且说真话的人设",
        "length_range": "100–250 字",
        "skeleton": [
            "【反常识结论】大多数人以为……其实恰恰相反",
            "【两点真相】拆出 2 个很少人挑明的底层原因",
            "【人话建议】说人话就是：现在直接怎么选/怎么做",
        ],
        "comment_hook": "评论区问一句：你身边是不是也有人踩过这个坑？",
    },
    "软性种草": {
        "code": "soft_promo",
        "goal": "价值先行，让有需求的人主动私信咨询，不被屏蔽",
        "length_range": "150–320 字",
        "skeleton": [
            "【高频提问】最近一周有好几个客户问我同一个问题……",
            "【免费解法】先给 3 条能直接照做的实操步骤",
            "【自然带出】如果懒得自己折腾，我们整理好的方案/服务直接配齐",
            "【低压力钩子】评论区留关键词或私信，发你一份参考清单",
        ],
        "comment_hook": "评论区直接放一个领取关键词或说明今日仅余名额",
    },
    "观点金句": {
        "code": "punchline",
        "goal": "短平快刷存在感，适合配随手拍或工作日常照",
        "length_range": "30–110 字",
        "skeleton": [
            "【一句判断】直接抛出反直觉或一针见血的结论",
            "【短补刀】1-2 句对比或比喻，点到为止",
        ],
        "comment_hook": "无需复杂首评，可附拍摄地点或一句话补充",
    },
    "信任背书": {
        "code": "trust_proof",
        "goal": "通过交付瞬间、老客户复购或长期坚持积累口碑",
        "length_range": "100–220 字",
        "skeleton": [
            "【真实瞬间】今天收到老客户消息 / 刚改完第 N 版方案",
            "【背后故事】提一句当初的顾虑和中间磨合",
            "【长期主义收尾】做这行第 N 年，越来越觉得靠谱比什么都值钱",
        ],
        "comment_hook": "感谢老客户信任，顺带一句欢迎有需要的朋友交流",
    },
}

WEEKLY_MIX_6DAYS = [
    ("Day 1 (周一)", "反常识破局", "08:30", "用行业真话定调本周专业度，抢早高峰通勤刷屏"),
    ("Day 2 (周二)", "实战案例", "12:15", "午休时间发真实客户解决过程与数据结果，建立成交信任"),
    ("Day 3 (周三)", "生活洞察", "20:30", "晚间松弛时段发生活切片+商业/专业联想，强化活人感"),
    ("Day 4 (周四)", "软性种草", "12:15", "先给3步干货再自然带出服务/清单，引导私信与评论"),
    ("Day 5 (周五)", "观点金句", "18:15", "下班前发短平快金句+随手拍，高赞不打扰"),
    ("Day 6 (周六/日)", "信任背书", "10:00", "周末发交付花絮/客户反馈/运动阅读日常，沉淀长期口碑"),
]


def resolve_industry(raw: str) -> str:
    """将用户输入或别名解析为标准 6 行业键名。"""
    key = raw.strip()
    for code, info in INDUSTRIES.items():
        if key == code or key in info["aliases"] or key == info["name"]:
            return code
    valid = ", ".join(f"{k}({v['name']})" for k, v in INDUSTRIES.items())
    raise ValueError(f"未识别的行业 '{raw}'。当前支持 6 大行业: {valid}")


def resolve_post_type(raw: str) -> str:
    """将文案类型解析为标准 6 大类型名称。"""
    key = raw.strip()
    if key in POST_TYPES:
        return key
    for name, info in POST_TYPES.items():
        if key == info["code"]:
            return name
    valid = ", ".join(POST_TYPES.keys())
    raise ValueError(f"未识别的文案类型 '{raw}'。支持类型: {valid}")


def build_brief(industry_code: str, post_type: str, topic: str, persona: str) -> dict[str, Any]:
    """构建单条朋友圈创作任务单。"""
    ind = INDUSTRIES[industry_code]
    pt = POST_TYPES[post_type]
    return {
        "industry_code": industry_code,
        "industry_name": ind["name"],
        "post_type": post_type,
        "topic": topic,
        "persona": persona or "一线实战派主理人（真诚、懂行、不装、说人话）",
        "target_audience": ind["audience"],
        "goal": pt["goal"],
        "length_range": pt["length_range"],
        "winning_angles": ind["winning_angles"],
        "structure_skeleton": pt["skeleton"],
        "audience_pitfall": ind["pitfalls"],
        "compliance_redline": ind["redlines"],
        "photo_suggestion": ind["photo_tips"],
        "recommended_times": ind["best_times"],
        "first_comment_hook": pt["comment_hook"],
        "format_rules": [
            "纯文本输出，严禁保留 **、##、- 等 Markdown 符号",
            "首行控制在 18-35 字内，确保手机端折叠前露出完整钩子",
            "每段 1-2 句话，段间空一行保持呼吸感",
            "单条 Emoji 不超过 2 个，严禁 AI 腔与机械工程黑话",
        ],
    }


def build_schedule(industry_code: str, days: int) -> dict[str, Any]:
    """构建 N 天朋友圈黄金配比排期表（默认 6 天）。"""
    ind = INDUSTRIES[industry_code]
    items = []
    for idx in range(days):
        day_label, ptype, post_time, rationale = WEEKLY_MIX_6DAYS[idx % len(WEEKLY_MIX_6DAYS)]
        pt = POST_TYPES[ptype]
        angle = ind["winning_angles"][idx % len(ind["winning_angles"])]
        items.append({
            "day": day_label,
            "post_type": ptype,
            "recommended_time": post_time,
            "suggested_angle": angle,
            "length_range": pt["length_range"],
            "rationale": rationale,
            "photo_tip": ind["photo_tips"],
        })
    return {
        "industry_code": industry_code,
        "industry_name": ind["name"],
        "days": days,
        "redline_reminder": ind["redlines"],
        "schedule": items,
    }


def render_brief_md(brief: dict[str, Any]) -> str:
    """将单条任务单格式化为易读 Markdown。"""
    lines = [
        f"# 朋友圈创作任务单｜{brief['industry_name']} · {brief['post_type']}",
        "",
        f"- **主题/素材**：{brief['topic']}",
        f"- **发圈人设**：{brief['persona']}",
        f"- **写给谁看**：{brief['target_audience']}",
        f"- **建议字数**：{brief['length_range']}（目标：{brief['goal']}）",
        f"- **建议时段**：{' / '.join(brief['recommended_times'])}",
        "",
        "## 一、行业高转化切口参考",
    ]
    for a in brief["winning_angles"]:
        lines.append(f"- {a}")
    lines.extend(["", "## 二、推荐结构骨架"])
    for step in brief["structure_skeleton"]:
        lines.append(f"1. {step}")
    lines.extend([
        "",
        "## 三、避坑与合规红线",
        f"- **受众错配避坑**：{brief['audience_pitfall']}",
        f"- **行业合规红线**：{brief['compliance_redline']}",
        "",
        "## 四、配图与首评建议",
        f"- **配图建议**：{brief['photo_suggestion']}",
        f"- **首评互动**：{brief['first_comment_hook']}",
        "",
        "## 五、出稿格式硬要求",
    ])
    for r in brief["format_rules"]:
        lines.append(f"- {r}")
    return "\n".join(lines)


def render_schedule_md(sched: dict[str, Any]) -> str:
    """将排期表格式化为易读 Markdown。"""
    lines = [
        f"# {sched['industry_name']} · {sched['days']} 天朋友圈黄金排期表",
        "",
        f"> 合规红线提醒：{sched['redline_reminder']}",
        "",
        "| 排期 | 内容类型 | 建议时间 | 字数区间 | 推荐切口 | 排期目的 |",
        "|---|---|---|---|---|---|",
    ]
    for it in sched["schedule"]:
        lines.append(
            f"| {it['day']} | {it['post_type']} | {it['recommended_time']} | "
            f"{it['length_range']} | {it['suggested_angle']} | {it['rationale']} |"
        )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="汇芯朋友圈文案规划器")
    parser.add_argument("--list-industries", action="store_true", help="列出支持的 6 大行业")
    parser.add_argument("--industry", default="ai", help="行业代码或名称（ai/tax/home/dental/legal/maternal）")
    parser.add_argument("--type", default="生活洞察", help="文案类型（生活洞察/实战案例/反常识破局/软性种草/观点金句/信任背书）")
    parser.add_argument("--topic", default="日常工作观察", help="核心素材或主题")
    parser.add_argument("--persona", default="", help="发圈人设补充描述")
    parser.add_argument("--schedule", action="store_true", help="生成多天黄金配比排期表")
    parser.add_argument("--days", type=int, default=6, help="排期天数（默认 6 天）")
    parser.add_argument("--format", choices=["md", "json"], default="md", help="输出格式")
    args = parser.parse_args()

    if args.list_industries:
        data = {k: {"name": v["name"], "audience": v["audience"], "redlines": v["redlines"]} for k, v in INDUSTRIES.items()}
        if args.format == "json":
            print(json.dumps(data, ensure_ascii=False, indent=2))
        else:
            for k, v in data.items():
                print(f"- {k}（{v['name']}）：受众={v['audience']}｜红线={v['redlines']}")
        return 0

    try:
        ind_code = resolve_industry(args.industry)
        if args.schedule:
            sched = build_schedule(ind_code, max(1, min(args.days, 14)))
            print(json.dumps(sched, ensure_ascii=False, indent=2) if args.format == "json" else render_schedule_md(sched))
        else:
            ptype = resolve_post_type(args.type)
            brief = build_brief(ind_code, ptype, args.topic, args.persona)
            print(json.dumps(brief, ensure_ascii=False, indent=2) if args.format == "json" else render_brief_md(brief))
        return 0
    except ValueError as exc:
        print(f"错误: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
