#!/usr/bin/env python3
"""
render.py — 通用周报渲染入口（Shell 注入框架统一入口）

用法：
  python scripts/render.py --data <json文件> --type <项目类型> [--output <输出路径>]
  python scripts/render.py --data <json文件> --type <项目类型> --dry-run
  python scripts/render.py --list-types

参数说明：
  --data      JSON 数据文件路径（必填）
  --type      项目类型（必填，见 --list-types 查看所有可用类型）
  --output    输出 HTML 文件路径（可选，默认自动生成）
  --dry-run   仅验证占位符替换，不写入文件
  --list-types 列出所有已注册的项目类型

Token 节省原理：
  大模型只需输出 JSON 数据文件（~100-200 行），本脚本负责渲染为完整 HTML。
  相比直接生成 HTML（~1000-2000 行），节省约 80-90% 输出 Token。

示例：
  # 渲染中台团队周报（platform 类型）
  python scripts/render.py \\
    --data state/w17_shell_data.json \\
    --type platform \\
    --output output/platform/weekly_report_2026-W17.html

  # 渲染增长团队周报（growth 类型）
  python scripts/render.py \\
    --data state/growth_w17.json \\
    --type growth \\
    --output output/growth-team/weekly_report_2026-W17.html

  # 列出所有支持的项目类型
  python scripts/render.py --list-types

  # 验证数据文件（不写入）
  python scripts/render.py --data state/w17_shell_data.json --type platform --dry-run
"""

import argparse
import json
import os
import sys
import warnings
from pathlib import Path
from datetime import datetime

# 确保 scripts 目录在 sys.path 中
SCRIPTS_DIR = Path(__file__).parent
SKILL_ROOT  = SCRIPTS_DIR.parent
sys.path.insert(0, str(SCRIPTS_DIR))

from shell_registry import REGISTRY, get_renderer, list_types, resolve_type


def parse_args():
    parser = argparse.ArgumentParser(
        description="通用周报 Shell 渲染器 — JSON 数据 → 完整 HTML",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument("--data",       help="JSON 数据文件路径")
    parser.add_argument("--type",       help="项目类型（使用 --list-types 查看所有可用类型）")
    parser.add_argument("--output",     help="输出 HTML 文件路径（可选）")
    parser.add_argument("--dry-run",    action="store_true", help="仅验证，不写入文件")
    parser.add_argument("--list-types", action="store_true", help="列出所有已注册的项目类型")
    return parser.parse_args()


def auto_detect_type(data: dict) -> str:
    """
    从 JSON 数据中自动推断项目类型。
    优先读取 meta.projectType 字段，其次根据数据结构特征推断。
    """
    # 1. 显式声明
    meta = data.get("meta", {})
    if "projectType" in meta:
        return meta["projectType"]

    # 2. 结构特征推断
    if "projects" in data and "improvements" in data:
        return "platform"
    if "companies" in data and "portfolio" in data:
        return "post-investment"
    if "extra" in data and "funnelMetrics" in data.get("extra", {}):
        return "growth"
    if "extra" in data and "features" in data.get("extra", {}):
        return "pre-launch"
    if "extra" in data and "activities" in data.get("extra", {}):
        return "ops"

    # 3. 默认
    return "general"


def resolve_output_path(data: dict, project_type: str, output_arg: str = None) -> Path:
    """自动生成输出路径（若未指定）。"""
    if output_arg:
        return Path(output_arg)

    meta   = data.get("meta", {})
    period = meta.get("reportPeriod", datetime.now().strftime("%Y-W%V"))
    period = period.replace("/", "-").replace(" ", "-")

    # 映射类型到输出子目录
    type_dir_map = {
        "platform":        "platform",
        "post-investment": "post-investment",
        "general":         "default",
        "growth":          "growth-team",
        "pre-launch":      "pre-launch",
        "ops":             "ops",
    }
    sub_dir = type_dir_map.get(project_type, project_type)
    out_dir = SKILL_ROOT / "output" / sub_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    return out_dir / f"weekly_report_{period}.html"


def render(data_path: str, project_type: str = None, output_path: str = None, dry_run: bool = False) -> str:
    """
    主渲染函数。

    Args:
        data_path:    JSON 数据文件路径
        project_type: 项目类型（None 时自动推断）
        output_path:  输出 HTML 文件路径（None 时自动生成）
        dry_run:      True 时仅验证，不写入文件

    Returns:
        输出文件的绝对路径（dry_run 时返回 "DRY_RUN"）
    """
    # 1. 读取数据
    data_file = Path(data_path)
    if not data_file.exists():
        raise FileNotFoundError(f"数据文件不存在: {data_path}")

    with open(data_file, encoding="utf-8") as f:
        data = json.load(f)

    # 2. 确定项目类型
    if project_type is None:
        project_type = auto_detect_type(data)
        print(f"[render] 自动推断项目类型: {project_type}")

    resolved_type = resolve_type(project_type)
    cfg = REGISTRY[resolved_type]

    print(f"[render] 项目类型: {resolved_type} ({cfg['desc']})")
    print(f"[render] Shell 模板: templates/shells/{cfg['shell']}")

    # 3. 特殊处理：platform 类型委托给 shell_injector.py
    if resolved_type == "platform":
        from shell_injector import render as _platform_render
        shell_path = str(SKILL_ROOT / "templates" / "shells" / cfg["shell"])
        html = _platform_render(data, shell_path)
    else:
        # 4. 通用路径：使用 shell_registry 中的渲染器
        renderer = get_renderer(resolved_type, data)
        html = renderer.render()

    # 5. dry-run 验证
    if dry_run:
        import re
        remaining = re.findall(r'\{\{[A-Z_]+\}\}', html)
        if remaining:
            print(f"[render] ⚠️  未替换占位符: {set(remaining)}")
        else:
            print("[render] ✅ 所有占位符已替换，验证通过")
        print(f"[render] 生成 HTML 大小: {len(html):,} 字节 / {html.count(chr(10)):,} 行")
        return "DRY_RUN"

    # 6. 写入文件
    out_path = resolve_output_path(data, resolved_type, output_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)

    size_kb = len(html) / 1024
    print(f"[render] ✅ 已生成: {out_path}")
    print(f"[render]    大小: {size_kb:.1f} KB / {html.count(chr(10)):,} 行")

    return str(out_path)


def main():
    args = parse_args()

    # 列出类型
    if args.list_types:
        list_types()
        return

    # 校验必填参数
    if not args.data:
        print("错误：请指定 --data 参数（JSON 数据文件路径）")
        print("使用 --list-types 查看所有支持的项目类型")
        sys.exit(1)

    if not args.type:
        print("[render] 未指定 --type，将自动推断项目类型...")

    try:
        result = render(
            data_path    = args.data,
            project_type = args.type,
            output_path  = args.output,
            dry_run      = args.dry_run,
        )
        if result != "DRY_RUN":
            print(f"\n✅ 周报生成完成！文件路径：{result}")
    except Exception as e:
        print(f"\n❌ 渲染失败：{e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
