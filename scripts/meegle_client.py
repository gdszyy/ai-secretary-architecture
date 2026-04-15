"""
Meegle API 客户端
负责与 Meegle 项目管理系统进行 API 交互，支持创建 Defect 工单、查询工作项等操作。
凭证信息通过环境变量读取：
  - MEEGLE_TOKEN: Meegle 个人访问令牌 (Personal Access Token)
  - MEEGLE_BASE_URL: Meegle API 基础 URL（默认 https://project.feishu.cn/open_api）
  - MEEGLE_PROJECT_KEY: 默认项目 Key（可在调用时覆盖）
"""

import os
import requests
import logging
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)


class MeegleClient:
    """
    Meegle (飞书项目) API 客户端。
    文档参考: https://project.feishu.cn/open_api
    """

    def __init__(
        self,
        token: Optional[str] = None,
        base_url: Optional[str] = None,
        project_key: Optional[str] = None,
    ):
        self.token = token or os.environ.get("MEEGLE_TOKEN")
        self.base_url = (
            base_url
            or os.environ.get("MEEGLE_BASE_URL", "https://project.feishu.cn/open_api")
        ).rstrip("/")
        self.project_key = project_key or os.environ.get("MEEGLE_PROJECT_KEY", "")

        if not self.token:
            raise ValueError(
                "MEEGLE_TOKEN must be provided or set in environment variables."
            )

    def _get_headers(self) -> Dict[str, str]:
        return {
            "X-USER-KEY": self.token,
            "Content-Type": "application/json",
        }

    def _request(
        self,
        method: str,
        path: str,
        payload: Optional[Dict] = None,
        params: Optional[Dict] = None,
    ) -> Dict:
        """通用 HTTP 请求封装，带重试逻辑（最多 3 次）。"""
        url = f"{self.base_url}{path}"
        for attempt in range(1, 4):
            try:
                resp = requests.request(
                    method,
                    url,
                    headers=self._get_headers(),
                    json=payload,
                    params=params,
                    timeout=15,
                )
                resp.raise_for_status()
                data = resp.json()
                # Meegle 业务层错误码
                if data.get("err_code", 0) != 0:
                    raise RuntimeError(
                        f"Meegle API error {data.get('err_code')}: {data.get('err_msg')}"
                    )
                return data
            except (requests.RequestException, RuntimeError) as exc:
                logger.warning("Meegle API attempt %d failed: %s", attempt, exc)
                if attempt == 3:
                    raise
        return {}

    # ------------------------------------------------------------------
    # 工作项 (Work Item) 相关接口
    # ------------------------------------------------------------------

    def create_work_item(
        self,
        project_key: Optional[str] = None,
        work_item_type_key: str = "defect",
        name: str = "",
        description: str = "",
        priority: str = "Medium",
        assignee_user_key: Optional[str] = None,
        extra_fields: Optional[Dict] = None,
    ) -> Dict:
        """
        在 Meegle 项目中创建工作项（默认类型为 defect）。

        Args:
            project_key: Meegle 项目 Key，不传则使用实例默认值。
            work_item_type_key: 工作项类型，如 'defect'、'story'、'task'。
            name: 工作项标题。
            description: 工作项描述（支持 Markdown）。
            priority: 优先级，枚举值 'Low' | 'Medium' | 'High' | 'Blocker'。
            assignee_user_key: 被指派人的 Meegle user_key。
            extra_fields: 其他自定义字段，将合并到 payload 中。

        Returns:
            创建成功的工作项数据字典，包含 work_item_id。
        """
        proj = project_key or self.project_key
        if not proj:
            raise ValueError("project_key is required.")

        payload: Dict[str, Any] = {
            "work_item_type_key": work_item_type_key,
            "name": name,
            "description": description,
            "priority": priority,
        }
        if assignee_user_key:
            payload["assignee"] = assignee_user_key
        if extra_fields:
            payload.update(extra_fields)

        data = self._request("POST", f"/{proj}/work_item", payload=payload)
        return data.get("data", {})

    def get_work_item(self, project_key: Optional[str] = None, work_item_id: str = "") -> Dict:
        """获取指定工作项详情。"""
        proj = project_key or self.project_key
        data = self._request("GET", f"/{proj}/work_item/{work_item_id}")
        return data.get("data", {})

    def update_work_item(
        self,
        project_key: Optional[str] = None,
        work_item_id: str = "",
        fields: Optional[Dict] = None,
    ) -> Dict:
        """更新工作项字段（如状态、指派人等）。"""
        proj = project_key or self.project_key
        data = self._request(
            "PUT", f"/{proj}/work_item/{work_item_id}", payload=fields or {}
        )
        return data.get("data", {})

    def list_work_items(
        self,
        project_key: Optional[str] = None,
        work_item_type_key: str = "defect",
        page_size: int = 50,
    ) -> List[Dict]:
        """列出项目下指定类型的工作项（分页获取全量）。"""
        proj = project_key or self.project_key
        all_items: List[Dict] = []
        page_num = 1

        while True:
            data = self._request(
                "GET",
                f"/{proj}/work_item/filter",
                params={
                    "work_item_type_key": work_item_type_key,
                    "page_size": page_size,
                    "page_num": page_num,
                },
            )
            items = data.get("data", {}).get("work_item_list", [])
            all_items.extend(items)
            if len(items) < page_size:
                break
            page_num += 1

        return all_items

    # ------------------------------------------------------------------
    # 用户查询接口
    # ------------------------------------------------------------------

    def query_user_by_email(self, email: str) -> Optional[str]:
        """
        通过邮箱查询 Meegle user_key。
        若未找到则返回 None。
        """
        try:
            data = self._request("GET", "/user/query", params={"email": email})
            users = data.get("data", {}).get("user_list", [])
            if users:
                return users[0].get("user_key")
        except Exception as exc:
            logger.warning("Failed to query Meegle user by email %s: %s", email, exc)
        return None
