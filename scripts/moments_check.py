#!/usr/bin/env python3
"""汇芯朋友圈文案质检与防折叠校验器（moments_check.py）

零外部依赖（纯 Python 3 标准库），执行 5 项把关：
1. 纯文本零乱码检查（拦截 **、##、- 列表等 Markdown 符号，支持 --clean 自动清理）；
2. 去 AI 味与去机械工程黑话检查；
3. 首行防截断（黄金 18-35 字）、总字数、分段呼吸感与 Emoji 数量检查；
4. 6 大行业合规红线与受众错配检查；
5. 双版本防折叠相似度对比（--compare）。
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

AI_CLICHES = [
    "在这个充满不确定性的时代",
    "在这个快节奏的时代",
    "让我们携手共创",
    "赋能",
    "抓手",
    "颗粒度",
    "生态位",
    "矩阵式",
    "破局点",
    "硬闸",
    "门闸",
    "机械硬闸",
    "流水线触发",
    "你值得拥有",
    "不看后悔",
]

INDUSTRY_REDLINES: dict[str, dict[str, Any]] = {
    "ai": {
        "name": "AI与一人公司",
        "forbidden": ["零门槛躺赚", "一键日入过万", "躺着赚钱", "稳赚不赔"],
        "advice_checks": [],
    },
    "tax": {
        "name": "财税企服",
        "forbidden": ["偷漏税", "虚开发票", "买发票", "绝对避税", "100%免税"],
        "advice_checks": [],
    },
    "home": {
        "name": "家装本地",
        "forbidden": ["全网最低价", "零增项保证", "终身免费换新"],
        "advice_checks": [
            ("报价/装修预算若未写清城市与面积（如㎡/平），同城业主难判断参考价值", r"(万|元|报价|预算)", r"(㎡|平|平米|平方|城市|北京|上海|杭州|台州|成都|深圳|广州|同城)"),
        ],
    },
    "dental": {
        "name": "口腔医美",
        "forbidden": ["最好", "第一", "根治", "无痛包好", "永久有效", "包治", "立竿见影", "零风险"],
        "advice_checks": [
            ("涉及口腔/医美诊疗或方案建议时，建议文末自然加上「具体方案以到院面诊检查为准」", r"(洗牙|补牙|正畸|种植|矫正|光子|热玛吉|水光|抗衰|项目|治疗)", r"(面诊|检查为准)"),
        ],
    },
    "legal": {
        "name": "法律咨询",
        "forbidden": ["包赢", "必离", "保证回款", "100%胜诉", "绝对赢"],
        "advice_checks": [],
    },
    "maternal": {
        "name": "母婴消费",
        "forbidden": ["医用级", "替代药品", "包治", "治疗作用", "根治湿疹"],
        "advice_checks": [],
    },
}

INDUSTRY_ALIASES: dict[str, str] = {
    "ai": "ai", "AI与一人公司": "ai", "一人公司": "ai",
    "tax": "tax", "财税企服": "tax", "财税": "tax",
    "home": "home", "家装本地": "home", "家装": "home",
    "dental": "dental", "口腔医美": "dental", "口腔": "dental", "医美": "dental",
    "legal": "legal", "法律咨询": "legal", "法律": "legal",
    "maternal": "maternal", "母婴消费": "maternal", "母婴": "maternal",
}

EMOJI_PATTERN = re.compile(
    "["
    "\U0001F300-\U0001F5FF"
    "\U0001F600-\U0001F64F"
    "\U0001F680-\U0001F6FF"
    "\U0001F900-\U0001F9FF"
    "\u2600-\u26FF"
    "\u2700-\u27BF"
    "]",
    flags=re.UNICODE,
)


def clean_markdown(text: str) -> str:
    """将文本中的常见 Markdown 符号清理为可直接发朋友圈的纯文本。"""
    lines = []
    for line in text.splitlines():
        s = re.sub(r"^#{1,6}\s+", "", line)
        s = re.sub(r"^[\-\*]\s+", "", s)
        s = re.sub(r"\*\*(.+?)\*\*", r"\1", s)
        s = re.sub(r"__(.+?)__", r"\1", s)
        s = re.sub(r"`([^`]+)`", r"\1", s)
        s = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", s)
        lines.append(s)
    return "\n".join(lines).strip()


def detect_markdown_artifacts(text: str) -> list[str]:
    """检测朋友圈文本中残留的 Markdown 符号。"""
    hits = []
    if re.search(r"(^|\n)#{1,6}\s+", text):
        hits.append("标题井号(#)")
    if re.search(r"\*\*[^*]+\*\*", text):
        hits.append("加粗星号(**)")
    if re.search(r"(^|\n)[\-\*]\s+", text):
        hits.append("无序列表符(- / *)")
    if "`" in text:
        hits.append("反引号(`)")
    if re.search(r"\[[^\]]+\]\([^)]+\)", text):
        hits.append("Markdown链接([text](url))")
    return hits


def char_ngrams(text: str, n: int = 2) -> set[str]:
    """提取去除空白与标点后的字符 n-gram 集合。"""
    norm = re.sub(r"[\s\W_]+", "", text)
    if len(norm) < n:
        return {norm} if norm else set()
    return {norm[i : i + n] for i in range(len(norm) - n + 1)}


def jaccard_similarity(a: str, b: str, n: int = 2) -> float:
    """计算两段中文文本的字符 n-gram Jaccard 相似度。"""
    sa = char_ngrams(a, n=n)
    sb = char_ngrams(b, n=n)
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / len(sa | sb)


def check_text(text: str, industry: str | None = None) -> dict[str, Any]:
    """对单条朋友圈文案进行全方位质检。"""
    errors: list[str] = []
    warnings: list[str] = []
    stripped = text.strip()
    total_chars = len(re.sub(r"\s+", "", stripped))
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", stripped) if p.strip()]
    first_para = paragraphs[0].splitlines()[0].strip() if paragraphs else ""
    first_len = len(re.sub(r"\s+", "", first_para))

    # 1. Markdown 符号检查
    md_hits = detect_markdown_artifacts(stripped)
    if md_hits:
        errors.append(f"检测到 Markdown 符号残留（{', '.join(md_hits)}），发朋友圈会原样暴露乱码，请转为纯文本。")

    # 2. 去 AI 味与去黑话检查
    cliche_hits = [w for w in AI_CLICHES if w in stripped]
    if cliche_hits:
        errors.append(f"检测到 AI 腔或工程黑话（{', '.join(cliche_hits)}），建议替换为大白话。")

    # 3. 长度与首行折叠检查
    if total_chars < 15:
        warnings.append(f"字数偏短（{total_chars} 字），若非极简打卡建议补充具体细节。")
    elif total_chars > 500:
        warnings.append(f"总字数 {total_chars} 字偏长，日常发圈建议控制在 80–350 字以内以提高完读率。")

    if first_len > 40:
        warnings.append(f"首行 {first_len} 字偏长（建议 15–35 字），手机端可能没说完就被折叠截断。")

    long_paras = [i + 1 for i, p in enumerate(paragraphs) if len(re.sub(r"\s+", "", p)) > 100]
    if long_paras:
        warnings.append(f"第 {long_paras} 段超过 100 字，建议拆成 1–2 句一段并空行，增加手机阅读呼吸感。")

    emoji_count = len(EMOJI_PATTERN.findall(stripped))
    if emoji_count > 3:
        warnings.append(f"使用了 {emoji_count} 个 Emoji，建议控制在 0–2 个以内，避免营销号感。")

    # 4. 行业合规红线检查
    ind_code = INDUSTRY_ALIASES.get(industry or "", "") if industry else ""
    if industry and not ind_code:
        warnings.append(f"未识别行业 '{industry}'，已跳过行业专属红线校验。")
    if ind_code:
        rules = INDUSTRY_REDLINES[ind_code]
        bad_terms = [t for t in rules["forbidden"] if t in stripped]
        if bad_terms:
            errors.append(f"[{rules['name']}] 触发行业红线词（{', '.join(bad_terms)}），必须修改。")
        for msg, trigger_pat, required_pat in rules["advice_checks"]:
            if re.search(trigger_pat, stripped) and not re.search(required_pat, stripped):
                warnings.append(f"[{rules['name']}] {msg}")

    return {
        "passed": len(errors) == 0,
        "industry": INDUSTRY_REDLINES[ind_code]["name"] if ind_code else "通用",
        "metrics": {
            "total_chars": total_chars,
            "paragraph_count": len(paragraphs),
            "first_line_chars": first_len,
            "emoji_count": emoji_count,
        },
        "errors": errors,
        "warnings": warnings,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="汇芯朋友圈文案质检与防折叠校验器")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--text", help="直接传入文案字符串")
    group.add_argument("--file", help="从文本文件读取文案")
    parser.add_argument("--industry", help="所属行业（ai/tax/home/dental/legal/maternal）")
    parser.add_argument("--compare", help="对比另一条文案文件，计算防折叠重合度")
    parser.add_argument("--clean", action="store_true", help="输出清理掉 Markdown 符号后的纯文本")
    parser.add_argument("--format", choices=["text", "json"], default="text", help="输出格式")
    args = parser.parse_args()

    raw_text = args.text if args.text is not None else Path(args.file).read_text(encoding="utf-8")
    if args.clean:
        print(clean_markdown(raw_text))
        return 0

    result = check_text(raw_text, industry=args.industry)

    if args.compare:
        other_text = Path(args.compare).read_text(encoding="utf-8")
        first_a = raw_text.strip().splitlines()[0] if raw_text.strip() else ""
        first_b = other_text.strip().splitlines()[0] if other_text.strip() else ""
        full_sim = round(jaccard_similarity(raw_text, other_text, n=2), 3)
        head_sim = round(jaccard_similarity(first_a, first_b, n=2), 3)
        fold_risk = full_sim >= 0.35 or head_sim >= 0.30
        result["anti_fold"] = {
            "bigram_similarity": full_sim,
            "first_line_similarity": head_sim,
            "fold_risk": fold_risk,
            "verdict": "存在被微信折叠风险，请按四层法改写开头与句式" if fold_risk else "差异度充足，可安全多号分发",
        }
        if fold_risk:
            result["errors"].append(f"防折叠校验未通过（全文相似度 {full_sim} / 首行相似度 {head_sim}）")
            result["passed"] = False

    if args.format == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        status = "✅ 通过" if result["passed"] else "❌ 未通过"
        m = result["metrics"]
        print(f"质检结果: {status} | 行业: {result['industry']} | 字数: {m['total_chars']} | 分段: {m['paragraph_count']} | 首行: {m['first_line_chars']}字 | Emoji: {m['emoji_count']}")
        for err in result["errors"]:
            print(f"  [必须修改] {err}")
        for warn in result["warnings"]:
            print(f"  [优化建议] {warn}")
        if "anti_fold" in result:
            af = result["anti_fold"]
            print(f"  [防折叠对比] 全文2-gram重合={af['bigram_similarity']} | 首行重合={af['first_line_similarity']} -> {af['verdict']}")

    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
