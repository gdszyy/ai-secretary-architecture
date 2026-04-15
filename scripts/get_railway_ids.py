"""
Railway 项目信息查询工具
========================
用途：帮助获取配置 GitHub Actions 所需的 RAILWAY_SERVICE_ID 和 RAILWAY_ENVIRONMENT_ID。

使用前提：
  1. 在 Railway 控制台生成 API Token（Account Settings → Tokens）
  2. 将 Token 设置为环境变量：export RAILWAY_API_TOKEN=your_token

运行方式：
  python3 scripts/get_railway_ids.py
"""

import os
import json
import requests

RAILWAY_API_URL = "https://backboard.railway.com/graphql/v2"


def query(token: str, gql: str, variables: dict = None) -> dict:
    resp = requests.post(
        RAILWAY_API_URL,
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        json={"query": gql, "variables": variables or {}},
        timeout=15,
    )
    resp.raise_for_status()
    data = resp.json()
    if "errors" in data:
        raise RuntimeError(f"GraphQL 错误: {data['errors']}")
    return data.get("data", {})


def main():
    token = os.environ.get("RAILWAY_API_TOKEN")
    if not token:
        print("❌ 请先设置环境变量 RAILWAY_API_TOKEN")
        print("   export RAILWAY_API_TOKEN=your_token_here")
        return

    print("🔍 正在查询 Railway 项目列表...\n")

    # 查询所有项目
    projects_data = query(token, """
        query {
            projects {
                edges {
                    node {
                        id
                        name
                        environments {
                            edges {
                                node {
                                    id
                                    name
                                }
                            }
                        }
                        services {
                            edges {
                                node {
                                    id
                                    name
                                }
                            }
                        }
                    }
                }
            }
        }
    """)

    projects = projects_data.get("projects", {}).get("edges", [])
    if not projects:
        print("⚠️  未找到任何项目，请确认 Token 权限是否正确。")
        return

    print(f"找到 {len(projects)} 个项目：\n")
    print("=" * 60)

    for p in projects:
        proj = p["node"]
        print(f"📁 项目名称: {proj['name']}")
        print(f"   项目 ID:   {proj['id']}")

        envs = proj.get("environments", {}).get("edges", [])
        print(f"   环境列表:")
        for e in envs:
            env = e["node"]
            print(f"     - {env['name']}: {env['id']}")

        services = proj.get("services", {}).get("edges", [])
        print(f"   服务列表:")
        for s in services:
            svc = s["node"]
            print(f"     - {svc['name']}: {svc['id']}")

        print()

    print("=" * 60)
    print("\n📋 请将以下值配置到 GitHub Secrets：")
    print("   RAILWAY_API_TOKEN  → 你的 Railway API Token")
    print("   RAILWAY_SERVICE_ID → 上方对应服务的 ID")
    print("   RAILWAY_ENVIRONMENT_ID → 上方对应环境（通常为 production）的 ID")
    print("\n配置路径：GitHub 仓库 → Settings → Secrets and variables → Actions → New repository secret")


if __name__ == "__main__":
    main()
