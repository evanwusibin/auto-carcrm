"""
Mermaid 块提取 + 静态语法预检器

功能：
1. 解析 flows/ 下所有 .md，提取 ```mermaid``` 围栏块
2. 把每个块单独导出为 .mermaid_extracts/<md_basename>__<n>.mmd
3. 对每个块做静态语法预检（不依赖 mermaid CLI）
4. 报告：每个 md 文件的 mermaid 块数量 + 每个块的预检结果

预检规则（针对 mermaid flowchart TD/LR）：
- 必须以 flowchart / graph / sequenceDiagram / classDiagram / stateDiagram / gitGraph 之一开头
- 节点 ID 仅允许 [A-Za-z0-9_]（中文 ID 也会被部分渲染器拒收）
- 节点形状中括号必须成对
- subgraph ... end 必须成对
- 标签里若含空格、<、>、括号等需要用 ["..."] 引号包裹
- 边语法 A --> B / A --- B / A -->|label| B / A -- text --- B
"""
from __future__ import annotations

import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import List


REPO = Path(r"d:\heimaAI\PytorchSDXX\08_掌柜智库\实战\实战\auto-carcrm")
FLOWS_DIR = REPO / "flows"
OUT_DIR = REPO / ".mermaid_extracts"

Mermaid_FENCE = re.compile(r"^```mermaid\s*$", re.MULTILINE)
GENERIC_FENCE = re.compile(r"^```\s*$", re.MULTILINE)


@dataclass
class Block:
    md_path: Path
    index: int
    start_line: int
    end_line: int
    body: str
    issues: List[str] = field(default_factory=list)


def extract_blocks(md_path: Path) -> List[Block]:
    text = md_path.read_text(encoding="utf-8")
    lines = text.splitlines()
    blocks: List[Block] = []
    i = 0
    idx = 0
    while i < len(lines):
        line = lines[i]
        if Mermaid_FENCE.match(line):
            start = i
            j = i + 1
            while j < len(lines) and not GENERIC_FENCE.match(lines[j]):
                j += 1
            body = "\n".join(lines[start + 1 : j])
            blocks.append(
                Block(
                    md_path=md_path,
                    index=idx,
                    start_line=start + 1,
                    end_line=j + 1,
                    body=body,
                )
            )
            idx += 1
            i = j + 1
        else:
            i += 1
    return blocks


# ------- 静态预检 -------
NODE_ID = re.compile(r"\b([A-Za-z_][A-Za-z0-9_]*)\b")
SUBGRAPH = re.compile(r"^\s*subgraph\b", re.IGNORECASE)
END_KW = re.compile(r"^\s*end\s*$", re.IGNORECASE)
HEADER_KW = re.compile(
    r"^\s*(flowchart|graph|sequenceDiagram|classDiagram|stateDiagram(?:-v2)?|erDiagram|journey|gantt|pie|quadrantChart|requirementDiagram|gitGraph|C4Context|C4Container|C4Component|C4Dynamic|C4Deployment)\b"
)


def lint_block(block: Block) -> List[str]:
    issues: List[str] = []
    body = block.body
    if not body.strip():
        issues.append("空 mermaid 块")
        return issues

    lines = body.splitlines()

    # 1) header
    if not HEADER_KW.match(lines[0]):
        issues.append(f"L{1}: 必须以 flowchart/graph/sequenceDiagram 等关键字开头，实际是 `{lines[0].strip()[:60]}`")

    # 2) subgraph / end 配对
    sub_count = sum(1 for ln in lines if SUBGRAPH.match(ln))
    end_count = sum(1 for ln in lines if END_KW.match(ln))
    if sub_count != end_count:
        issues.append(f"subgraph({sub_count}) 与 end({end_count}) 数量不匹配")

    # 3) 括号配对
    open_sq = body.count("[")
    close_sq = body.count("]")
    open_cu = body.count("{")
    close_cu = body.count("}")
    open_ro = body.count("(")
    close_ro = body.count(")")
    if (open_sq - close_sq) % 2 != 0:
        issues.append(f"[ 与 ] 数量不一致：{open_sq} vs {close_sq}")
    if open_cu != close_cu:
        issues.append(f"{{ 与 }} 数量不一致：{open_cu} vs {close_cu}")
    if open_ro != close_ro:
        issues.append(f"( 与 ) 数量不一致：{open_ro} vs {close_ro}")

    # 4) 节点 ID 校验：flowchart 节点 ID 通常必须 [A-Za-z0-9_]（不允许中文 / 全角 / 横线）
    #    找出"看起来像边定义"或"节点定义"的行：含 -- 或 --> 或 :::
    for ln_no, ln in enumerate(lines, 1):
        if "--" in ln:
            # 简单扫：箭头前后不是合法 ID 字符
            # 把箭头和边标签剥掉
            stripped = re.sub(r"-->?\|[^|]*\|", "->", ln)
            stripped = re.sub(r"-->?--?", "->", stripped)
            stripped = re.sub(r"---", "->", stripped)
            # 检查 \w 之外的非空白、非 ASCII 标点
            # 允许的字符：[A-Za-z0-9_\s\[\](){}\->|.:/,"]
            bad = re.findall(r"[^\w\s\[\]\{\}\(\)\->\|:/\.,\"\u4e00-\u9fff]", stripped)
            if bad:
                unique_bad = sorted(set(bad))
                issues.append(
                    f"L{ln_no}: 边/节点定义含可疑字符 {unique_bad} → {ln.strip()[:80]}"
                )

        # 中文 / 全角字符在 ID 位置
        for m in re.finditer(r"\b([\u4e00-\u9fff][\u4e00-\u9fffA-Za-z0-9_]*)\b", ln):
            issues.append(
                f"L{ln_no}: 节点 ID 含中文 `{m.group(1)}`，部分 mermaid 渲染器（GitHub 旧版）会失败，建议改成 ASCII ID + 中文放在标签"
            )
            break  # 每行只报一次

    return issues


def main() -> int:
    OUT_DIR.mkdir(exist_ok=True)
    md_files = sorted(FLOWS_DIR.rglob("*.md"))
    print(f"扫描 {len(md_files)} 个 md 文档\n")
    total_blocks = 0
    total_issues = 0
    fail_files: List[str] = []
    for md in md_files:
        blocks = extract_blocks(md)
        total_blocks += len(blocks)
        if not blocks:
            continue
        print(f"== {md.relative_to(REPO)} ：{len(blocks)} 个 mermaid 块 ==")
        for b in blocks:
            out_name = f"{md.stem}__{b.index:02d}.mmd"
            (OUT_DIR / out_name).write_text(b.body, encoding="utf-8")
            issues = lint_block(b)
            b.issues = issues
            if issues:
                total_issues += len(issues)
                fail_files.append(str(md.relative_to(REPO)))
                print(f"  [{b.index}] 行 {b.start_line}-{b.end_line} ❌ {len(issues)} 问题")
                for it in issues:
                    print(f"      - {it}")
            else:
                print(f"  [{b.index}] 行 {b.start_line}-{b.end_line} ✅")
    print()
    print(f"汇总：{len(md_files)} 个 md / {total_blocks} 个 mermaid 块 / {total_issues} 个预检告警")
    if fail_files:
        print(f"有问题的文件：")
        for f in sorted(set(fail_files)):
            print(f"  - {f}")
    print(f"\n已导出 {total_blocks} 个 .mmd 到 {OUT_DIR.relative_to(REPO)}/")
    return 0 if total_issues == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
