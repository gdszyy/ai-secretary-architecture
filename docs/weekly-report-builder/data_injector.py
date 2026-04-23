"""
data_injector.py — 周报数据注入器

功能：
  读取 data_schema.json（或任意符合 DashboardData 结构的 JSON 文件），
  将其注入到 weekly_report_example.tsx 的 mockData 块，生成新版周报 tsx 文件。
  UI 代码（组件/样式/布局）完全不变，只替换数据层。

用法：
  python scripts/data_injector.py \\
      --data templates/data_schema.json \\
      --template templates/weekly_report_example.tsx \\
      --output output/weekly_report_2026-W17.tsx

  # 快捷模式（自动推断输出文件名）
  python scripts/data_injector.py --data templates/data_schema.json

参数：
  --data      必填，输入 JSON 数据文件路径
  --template  可选，tsx 模板路径（默认 templates/weekly_report_example.tsx）
  --output    可选，输出文件路径（默认 output/weekly_report_{reportPeriod}.tsx）
  --dry-run   仅打印将要替换的 mockData 块，不写文件
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

# ─── 常量 ────────────────────────────────────────────────────────────────────

SKILL_ROOT = Path(__file__).parent.parent
DEFAULT_TEMPLATE = SKILL_ROOT / "templates" / "weekly_report_example.tsx"
DEFAULT_OUTPUT_DIR = SKILL_ROOT / "output"

# mockData 块的起止标记（与 weekly_report_example.tsx 中的注释对齐）
MOCK_DATA_START = "// ⚠️  以下 mockData 由 weekly-report-builder 代码生成引擎自动注入"
MOCK_DATA_VAR   = "const mockData: DashboardData = "
MOCK_DATA_END_MARKER = "};\n// ─────────────────────────────────────────────────────────────────────────────\n// Section 4:"


# ─── 核心函数 ─────────────────────────────────────────────────────────────────

def load_data(data_path: str) -> dict:
    """加载并验证 JSON 数据文件。"""
    with open(data_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # 去除注释字段
    data.pop("_comment", None)
    data.pop("_usage", None)

    # 基础字段校验
    required = ["meta", "healthScore", "northStar", "kpiAlerts", "kpiMetrics", "milestones", "modules"]
    missing = [k for k in required if k not in data]
    if missing:
        raise ValueError(f"JSON 数据缺少必填字段: {missing}")

    return data


def data_to_tsx_literal(data: dict, indent: int = 0) -> str:
    """
    将 Python dict/list 转换为 TypeScript 对象字面量字符串。
    保留中文字符，数字不加引号，布尔值使用 true/false。
    """
    pad = "  " * indent

    if isinstance(data, dict):
        if not data:
            return "{}"
        lines = ["{"]
        items = list(data.items())
        for i, (k, v) in enumerate(items):
            comma = "," if i < len(items) - 1 else ""
            val_str = data_to_tsx_literal(v, indent + 1)
            lines.append(f"{pad}  {k}: {val_str}{comma}")
        lines.append(f"{pad}}}")
        return "\n".join(lines)

    elif isinstance(data, list):
        if not data:
            return "[]"
        lines = ["["]
        for i, item in enumerate(data):
            comma = "," if i < len(data) - 1 else ""
            val_str = data_to_tsx_literal(item, indent + 1)
            lines.append(f"{pad}  {val_str}{comma}")
        lines.append(f"{pad}]")
        return "\n".join(lines)

    elif isinstance(data, bool):
        return "true" if data else "false"

    elif isinstance(data, (int, float)):
        return str(data)

    elif data is None:
        return "undefined"

    else:
        # 字符串：转义反斜杠和单引号，使用单引号包裹
        escaped = str(data).replace("\\", "\\\\").replace("'", "\\'")
        return f"'{escaped}'"


def build_mock_data_block(data: dict) -> str:
    """生成完整的 mockData 块字符串。"""
    period = data.get("meta", {}).get("reportPeriod", "unknown")
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    header = (
        f"// ⚠️  以下 mockData 由 weekly-report-builder 代码生成引擎自动注入\n"
        f"// 报告周期: {period} | 注入时间: {now}\n"
        f"// 如需修改数据，请编辑 templates/data_schema.json 后重新运行 data_injector.py\n"
    )

    tsx_literal = data_to_tsx_literal(data)
    mock_block = f"const mockData: DashboardData = {tsx_literal};\n"

    return header + mock_block


def inject(template_path: str, data: dict, output_path: str, dry_run: bool = False) -> str:
    """
    将数据注入模板，返回注入后的完整 tsx 内容。
    使用正则精准定位 mockData 块的起止位置。
    """
    with open(template_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 定位 mockData 块：从 MOCK_DATA_START 注释到 "};\n// Section 4:" 之前
    # 使用正则匹配，支持注释行数变化
    pattern = re.compile(
        r"(// ⚠️  以下 mockData 由 weekly-report-builder.*?)"  # 注释头（非贪婪）
        r"(const mockData: DashboardData = \{.*?\};\n)"        # mockData 对象
        r"(?=// ─+\n// Section 4:)",                           # 向前看 Section 4 标记
        re.DOTALL
    )

    match = pattern.search(content)
    if not match:
        # 降级：直接找 const mockData: DashboardData = { 到 }; 的范围
        start_marker = "const mockData: DashboardData = {"
        start_idx = content.find(start_marker)
        if start_idx == -1:
            raise ValueError("未在模板中找到 'const mockData: DashboardData = {' 标记，请确认模板文件正确。")

        # 找到对应的闭合 };
        brace_depth = 0
        i = start_idx + len("const mockData: DashboardData = ")
        end_idx = -1
        for j in range(i, len(content)):
            if content[j] == "{":
                brace_depth += 1
            elif content[j] == "}":
                brace_depth -= 1
                if brace_depth == 0:
                    end_idx = j + 1  # 包含 }
                    # 跳过后面的 ;
                    if end_idx < len(content) and content[end_idx] == ";":
                        end_idx += 1
                    break

        if end_idx == -1:
            raise ValueError("未能找到 mockData 块的结束位置，请检查模板文件的括号匹配。")

        # 找到注释起始行
        comment_start = content.rfind("\n// ⚠️", 0, start_idx)
        if comment_start == -1:
            comment_start = start_idx
        else:
            comment_start += 1  # 跳过 \n

        replace_start = comment_start
        replace_end = end_idx
    else:
        replace_start = match.start()
        replace_end = match.end()

    new_block = build_mock_data_block(data)

    if dry_run:
        print("=" * 60)
        print("【DRY RUN】将替换以下内容：")
        print("=" * 60)
        print(content[replace_start:replace_end])
        print("=" * 60)
        print("【替换为】：")
        print("=" * 60)
        print(new_block)
        return content

    new_content = content[:replace_start] + new_block + "\n" + content[replace_end:]

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(new_content)

    return new_content


# ─── CLI 入口 ─────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="周报数据注入器：将 JSON 数据注入 tsx 模板，生成新版周报"
    )
    parser.add_argument("--data",     required=True, help="输入 JSON 数据文件路径")
    parser.add_argument("--template", default=str(DEFAULT_TEMPLATE), help="tsx 模板路径")
    parser.add_argument("--output",   default=None,  help="输出 tsx 文件路径（默认自动推断）")
    parser.add_argument("--dry-run",  action="store_true", help="仅预览替换内容，不写文件")
    args = parser.parse_args()

    # 加载数据
    try:
        data = load_data(args.data)
    except (FileNotFoundError, json.JSONDecodeError, ValueError) as e:
        print(f"❌ 数据加载失败: {e}", file=sys.stderr)
        sys.exit(1)

    # 推断输出路径
    if args.output is None:
        period = data.get("meta", {}).get("reportPeriod", "unknown").replace("/", "-")
        output_path = str(DEFAULT_OUTPUT_DIR / f"weekly_report_{period}.tsx")
    else:
        output_path = args.output

    # 执行注入
    try:
        inject(args.template, data, output_path, dry_run=args.dry_run)
    except (FileNotFoundError, ValueError) as e:
        print(f"❌ 注入失败: {e}", file=sys.stderr)
        sys.exit(1)

    if not args.dry_run:
        print(f"✅ 周报已生成: {output_path}")
        print(f"   报告周期: {data['meta']['reportPeriod']}")
        print(f"   项目名称: {data['meta']['projectName']}")
        print(f"   模块数量: {len(data.get('modules', []))}")
        print(f"   KPI 指标: {len(data.get('kpiMetrics', []))}")
        print(f"   里程碑数: {len(data.get('milestones', []))}")


if __name__ == "__main__":
    main()
