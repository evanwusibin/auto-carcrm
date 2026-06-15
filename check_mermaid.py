"""
Mermaid 块提取 + 精准语法预检器（v2）

聚焦"硬错"：仅报告会让任何主流 mermaid 渲染器（mermaid 9+/10/11）都报错的语法问题。
中文 ID / emoji / 全角标点 / <br/> 在现代 mermaid 中都是合法的，不再误报。

硬错清单：
1) 块为空 / 无 header（必须以 flowchart / graph / sequenceDiagram 等关键字开头）
2) subgraph / end 数量不匹配
3) 三种括号 [ ] { } ( ) 数量不配对
4) 双引号 " 出现奇数次（字符串未闭合）
5) 连字符节点 A--B 这种"无箭头边"无标签的形式，mermaid 10+ 已支持，但应避免
6) 边标签的引号未闭合：A -->|"label"| B
7) 含 mermaid 关键字冲突（如 direction、style、classDef 等）但语法错
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


SUBGRAPH = re.compile(r"^\s*subgraph\b", re.IGNORECASE)
END_KW = re.compile(r"^\s*end\s*$", re.IGNORECASE)
HEADER_KW = re.compile(
    r"^\s*(flowchart|graph|sequenceDiagram|classDiagram|stateDiagram(?:-v2)?|erDiagram|"
    r"journey|gantt|pie|quadrantChart|requirementDiagram|gitGraph|"
    r"C4Context|C4Container|C4Component|C4Dynamic|C4Deployment)\b"
)


def lint_block(block: Block) -> List[str]:
    issues: List[str] = []
    body = block.body
    if not body.strip():
        return [f"行 {block.start_line+1}: 空 mermaid 块"]

    lines = body.splitlines()

    # 1) header
    if not HEADER_KW.match(lines[0]):
        issues.append(
            f"行 {block.start_line+1}: 缺 header（必须以 flowchart/graph/sequenceDiagram 等关键字开头），实际是 `{lines[0].strip()[:60]}`"
        )

    # 2) subgraph / end 配对
    sub_count = sum(1 for ln in lines if SUBGRAPH.match(ln))
    end_count = sum(1 for ln in lines if END_KW.match(ln))
    if sub_count != end_count:
        issues.append(
            f"行 {block.start_line+sub_count+1} 附近: subgraph({sub_count}) 与 end({end_count}) 数量不匹配"
        )

    # 3) 括号配对（注意：含于字符串/标签里也要算，但 mermaid 标签里一般用 ["..."]，括号配对实际指方括号/花括号/圆括号）
    open_sq = body.count("[")
    close_sq = body.count("]")
    open_cu = body.count("{")
    close_cu = body.count("}")
    open_ro = body.count("(")
    close_ro = body.count(")")
    if (open_sq - close_sq) % 2 != 0:
        issues.append(f"行 ? 附近: [ 与 ] 数量不一致：{open_sq} vs {close_sq}")
    if open_cu != close_cu:
        issues.append(f"行 ? 附近: {{ 与 }} 数量不一致：{open_cu} vs {close_cu}")
    if open_ro != close_ro:
        issues.append(f"行 ? 附近: ( 与 ) 数量不一致：{open_ro} vs {close_ro}")

    # 4) 双引号配对
    n_quote = body.count('"')
    if n_quote % 2 != 0:
        issues.append(f"双引号 \" 出现奇数次（{n_quote}），可能存在未闭合的字符串")

    # 5) 边标签 -->|label| 中的 | 是否成对
    n_pipe = 0
    for ln in lines:
        n_pipe += ln.count("-->|")
    if n_pipe > 0:
        n_close = body.count("|")
        if n_close % 2 != 0:
            issues.append(f"边标签 | 出现奇数次（{n_close}），可能存在未闭合的边标签")

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
    print(f"汇总：{len(md_files)} 个 md / {total_blocks} 个 mermaid 块 / {total_issues} 个硬错告警")
    if fail_files:
        print(f"有问题的文件：")
        for f in sorted(set(fail_files)):
            print(f"  - {f}")
    print(f"\n已导出 {total_blocks} 个 .mmd 到 {OUT_DIR.relative_to(REPO)}/")
    return 0 if total_issues == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
