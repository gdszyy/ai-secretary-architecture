"""
data_injector.py — 周报数据注入器（多项目版）

功能：
  读取项目 schema.json，将数据注入到对应项目的 tsx 模板，生成新版周报。
  UI 代码（组件/样式/布局）完全不变，只替换数据层。

用法：
  # 多项目模式（推荐）：通过 --project 自动路由
  python scripts/data_injector.py --project post-investment
  python scripts/data_injector.py --project platform
  python scripts/data_injector.py --project default

  # 兼容旧模式：手动指定数据文件和模板
  python scripts/data_injector.py \\
      --data templates/data_schema.json \\
      --template templates/weekly_report_example.tsx \\
      --output output/weekly_report_2026-W17.tsx

  # 列出所有可用项目
  python scripts/data_injector.py --list-projects

  # 预览模式（不写文件）
  python scripts/data_injector.py --project platform --dry-run

参数：
  --project       多项目模式：指定项目 ID（对应 projects/{id}/ 目录）
  --data          兼容模式：输入 JSON 数据文件路径（与 --project 二选一）
  --template      可选，tsx 模板路径（--project 模式下从 config.json 读取）
  --output        可选，输出文件路径（默认自动推断）
  --dry-run       仅打印将要替换的 mockData 块，不写文件
  --list-projects 列出所有可用项目
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

# ─── 常量 ────────────────────────────────────────────────────────────────────

SKILL_ROOT    = Path(__file__).parent.parent
PROJECTS_DIR  = SKILL_ROOT / "projects"
DEFAULT_TEMPLATE = SKILL_ROOT / "templates" / "weekly_report_example.tsx"
DEFAULT_OUTPUT_DIR = SKILL_ROOT / "output"


# ─── 项目路由 ─────────────────────────────────────────────────────────────────

def list_projects() -> list[dict]:
    """列出所有可用项目（projects/ 目录下含 config.json 的子目录）。"""
    projects = []
    if not PROJECTS_DIR.exists():
        return projects
    for d in sorted(PROJECTS_DIR.iterdir()):
        config_path = d / "config.json"
        if d.is_dir() and config_path.exists():
            try:
                with open(config_path, encoding="utf-8") as f:
                    cfg = json.load(f)
                projects.append({
                    "id":          cfg.get("id", d.name),
                    "name":        cfg.get("name", d.name),
                    "description": cfg.get("description", ""),
                    "path":        str(d),
                })
            except Exception:
                pass
    return projects


def load_project_config(project_id: str) -> dict:
    """加载项目配置文件。"""
    project_dir = PROJECTS_DIR / project_id
    config_path = project_dir / "config.json"

    if not project_dir.exists():
        available = [d.name for d in PROJECTS_DIR.iterdir() if d.is_dir()] if PROJECTS_DIR.exists() else []
        raise FileNotFoundError(
            f"项目 '{project_id}' 不存在。可用项目：{available}\n"
            f"使用 --list-projects 查看所有项目，或用 project_scaffold.py 创建新项目。"
        )
    if not config_path.exists():
        raise FileNotFoundError(f"项目 '{project_id}' 缺少 config.json：{config_path}")

    with open(config_path, encoding="utf-8") as f:
        config = json.load(f)

    # 解析相对路径（相对于项目目录）
    config["_project_dir"] = str(project_dir)

    template_raw = config.get("template", "../../templates/weekly_report_example.tsx")
    config["_template_path"] = str((project_dir / template_raw).resolve())

    schema_raw = config.get("schema", "schema.json")
    config["_schema_path"] = str((project_dir / schema_raw).resolve())

    state_dir_raw = config.get("stateDir", "../../state")
    config["_state_dir"] = str((project_dir / state_dir_raw).resolve())

    output_dir_raw = config.get("outputDir", "../../output")
    config["_output_dir"] = str((project_dir / output_dir_raw).resolve())

    return config


# ─── 数据加载 ─────────────────────────────────────────────────────────────────

def _strip_comments(obj):
    """递归去除所有以 _ 开头的注释字段。"""
    if isinstance(obj, dict):
        return {k: _strip_comments(v) for k, v in obj.items() if not k.startswith("_")}
    elif isinstance(obj, list):
        return [_strip_comments(i) for i in obj]
    return obj


def load_data(data_path: str) -> dict:
    """加载并验证 JSON 数据文件。"""
    with open(data_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    data = _strip_comments(data)

    # 基础字段校验
    required = ["meta", "healthScore", "northStar", "kpiAlerts", "kpiMetrics", "milestones", "modules"]
    missing = [k for k in required if k not in data]
    if missing:
        raise ValueError(f"JSON 数据缺少必填字段: {missing}")

    return data


# ─── TSX 字面量生成 ───────────────────────────────────────────────────────────

def data_to_tsx_literal(data, indent: int = 0) -> str:
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
        escaped = str(data).replace("\\", "\\\\").replace("'", "\\'")
        return f"'{escaped}'"


def build_mock_data_block(data: dict, schema_path: str = "") -> str:
    """生成完整的 mockData 块字符串。"""
    period   = data.get("meta", {}).get("reportPeriod", "unknown")
    project  = data.get("meta", {}).get("projectName", "")
    now      = datetime.now().strftime("%Y-%m-%d %H:%M")
    src_hint = f" | 数据来源: {schema_path}" if schema_path else ""

    header = (
        f"// ⚠️  以下 mockData 由 weekly-report-builder 代码生成引擎自动注入\n"
        f"// 报告周期: {period} | 项目: {project} | 注入时间: {now}{src_hint}\n"
        f"// 如需修改数据，请编辑对应项目的 schema.json 后重新运行 data_injector.py\n"
    )

    tsx_literal = data_to_tsx_literal(data)
    mock_block  = f"const mockData: DashboardData = {tsx_literal};\n"

    return header + mock_block


# ─── 注入核心 ─────────────────────────────────────────────────────────────────

def inject(template_path: str, data: dict, output_path: str,
           dry_run: bool = False, schema_path: str = "") -> str:
    """
    将数据注入模板，返回注入后的完整 tsx 内容。
    使用正则精准定位 mockData 块的起止位置。
    """
    with open(template_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 定位 mockData 块：从注入注释到 "};\n// Section 4:" 之前
    pattern = re.compile(
        r"(// ⚠️  以下 mockData 由 weekly-report-builder.*?)"
        r"(const mockData: DashboardData = \{.*?\};\n)"
        r"(?=// ─+\n// Section 4:)",
        re.DOTALL
    )

    match = pattern.search(content)
    if not match:
        # 降级：直接找 const mockData: DashboardData = { 到 }; 的范围
        start_marker = "const mockData: DashboardData = {"
        start_idx = content.find(start_marker)
        if start_idx == -1:
            raise ValueError(
                "未在模板中找到 'const mockData: DashboardData = {' 标记，"
                "请确认模板文件正确。"
            )

        brace_depth = 0
        i = start_idx + len("const mockData: DashboardData = ")
        end_idx = -1
        for j in range(i, len(content)):
            if content[j] == "{":
                brace_depth += 1
            elif content[j] == "}":
                brace_depth -= 1
                if brace_depth == 0:
                    end_idx = j + 1
                    if end_idx < len(content) and content[end_idx] == ";":
                        end_idx += 1
                    break

        if end_idx == -1:
            raise ValueError("未能找到 mockData 块的结束位置，请检查模板文件的括号匹配。")

        comment_start = content.rfind("\n// ⚠️", 0, start_idx)
        replace_start = (comment_start + 1) if comment_start != -1 else start_idx
        replace_end   = end_idx
    else:
        replace_start = match.start()
        replace_end   = match.end()

    new_block = build_mock_data_block(data, schema_path)

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

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(new_content)

    return new_content


# ─── CLI 入口 ─────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="周报数据注入器：将 JSON 数据注入 tsx 模板，生成新版周报",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例：
  python scripts/data_injector.py --project post-investment
  python scripts/data_injector.py --project platform --dry-run
  python scripts/data_injector.py --list-projects
  python scripts/data_injector.py --data templates/data_schema.json  # 兼容旧模式
        """
    )
    parser.add_argument("--project",       default=None,  help="项目 ID（对应 projects/{id}/ 目录）")
    parser.add_argument("--data",          default=None,  help="兼容模式：JSON 数据文件路径")
    parser.add_argument("--template",      default=None,  help="tsx 模板路径（可选覆盖）")
    parser.add_argument("--output",        default=None,  help="输出 tsx 文件路径（默认自动推断）")
    parser.add_argument("--dry-run",       action="store_true", help="仅预览替换内容，不写文件")
    parser.add_argument("--list-projects", action="store_true", help="列出所有可用项目")
    args = parser.parse_args()

    # ── 列出项目 ──────────────────────────────────────────────────────────────
    if args.list_projects:
        projects = list_projects()
        if not projects:
            print("暂无可用项目。使用 project_scaffold.py 创建新项目。")
            return
        print(f"{'ID':<20} {'名称':<20} 描述")
        print("─" * 80)
        for p in projects:
            desc = p["description"][:40] + "..." if len(p["description"]) > 40 else p["description"]
            print(f"{p['id']:<20} {p['name']:<20} {desc}")
        return

    # ── 参数校验 ──────────────────────────────────────────────────────────────
    if not args.project and not args.data:
        parser.error("必须指定 --project 或 --data 之一。使用 --list-projects 查看可用项目。")

    # ── 多项目模式 ────────────────────────────────────────────────────────────
    if args.project:
        try:
            config = load_project_config(args.project)
        except FileNotFoundError as e:
            print(f"❌ {e}", file=sys.stderr)
            sys.exit(1)

        data_path     = config["_schema_path"]
        template_path = args.template or config["_template_path"]
        output_dir    = config["_output_dir"]

        try:
            data = load_data(data_path)
        except (FileNotFoundError, json.JSONDecodeError, ValueError) as e:
            print(f"❌ 数据加载失败: {e}", file=sys.stderr)
            sys.exit(1)

        if args.output is None:
            period = data.get("meta", {}).get("reportPeriod", "unknown").replace("/", "-")
            output_path = str(Path(output_dir) / f"weekly_report_{period}.tsx")
        else:
            output_path = args.output

    # ── 兼容旧模式 ────────────────────────────────────────────────────────────
    else:
        data_path     = args.data
        template_path = args.template or str(DEFAULT_TEMPLATE)

        try:
            data = load_data(data_path)
        except (FileNotFoundError, json.JSONDecodeError, ValueError) as e:
            print(f"❌ 数据加载失败: {e}", file=sys.stderr)
            sys.exit(1)

        if args.output is None:
            period = data.get("meta", {}).get("reportPeriod", "unknown").replace("/", "-")
            output_path = str(DEFAULT_OUTPUT_DIR / f"weekly_report_{period}.tsx")
        else:
            output_path = args.output

    # ── 执行注入 ──────────────────────────────────────────────────────────────
    try:
        inject(template_path, data, output_path,
               dry_run=args.dry_run, schema_path=data_path)
    except (FileNotFoundError, ValueError) as e:
        print(f"❌ 注入失败: {e}", file=sys.stderr)
        sys.exit(1)

    if not args.dry_run:
        project_label = f"[{args.project}] " if args.project else ""
        print(f"✅ {project_label}周报已生成: {output_path}")
        print(f"   报告周期: {data['meta']['reportPeriod']}")
        print(f"   项目名称: {data['meta']['projectName']}")
        print(f"   模块数量: {len(data.get('modules', []))}")
        print(f"   KPI 指标: {len(data.get('kpiMetrics', []))}")
        print(f"   里程碑数: {len(data.get('milestones', []))}")
        if "extra" in data:
            print(f"   扩展字段: extra（含项目特有数据，可用于定制组件）")


if __name__ == "__main__":
    main()
