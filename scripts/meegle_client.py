'''
Meegle Open API Python 客户端

支持 plugin_token（生产）和 virtual_token（开发调试）两种模式。
经过实际 API 探测验证，修正了正确的端点路径。
'''

import requests
import time
import logging
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)


class MeegleAPIClient:
    """Meegle Open API 客户端，支持自动刷新 token、请求重试和速率限制。"""

    def __init__(self, domain: str, plugin_id: str, plugin_secret: str,
                 user_key: str, token_type: int = 0):
        '''
        初始化客户端

        :param domain: Meegle 域名，如 "meegle.com"
        :param plugin_id: 插件 ID
        :param plugin_secret: 插件密钥
        :param user_key: 执行 API 操作的用户 Key（需是插件 master 才能使用 virtual_token）
        :param token_type: 0=plugin_token（生产环境），1=virtual_token（开发调试）
        '''
        self.base_url = f"https://{domain}/open_api"
        self.plugin_id = plugin_id
        self.plugin_secret = plugin_secret
        self.user_key = user_key
        self.token_type = token_type
        self._token = None
        self._token_expire_at = 0

        logger.info(f"[Meegle] 初始化客户端: domain={domain}, token_type={'virtual' if token_type == 1 else 'plugin'}")

    def _get_token(self) -> str:
        """获取并缓存 token（自动刷新）"""
        if self._token and time.time() < self._token_expire_at - 300:
            return self._token

        url = f"{self.base_url}/authen/plugin_token"
        payload = {
            "plugin_id": self.plugin_id,
            "plugin_secret": self.plugin_secret,
            "type": self.token_type
        }

        logger.info("[Meegle] 正在获取新 token...")
        response = requests.post(
            url, headers={"Content-Type": "application/json"},
            json=payload, timeout=10
        )
        response.raise_for_status()

        data = response.json()
        err_code = data.get("err_code", data.get("error", {}).get("code", -1))
        if err_code != 0:
            msg = data.get("err_msg", data.get("error", {}).get("msg", "未知错误"))
            raise Exception(f"[Meegle] 获取 token 失败: {msg}")

        self._token = data["data"]["token"]
        expire = data["data"].get("expire_time", 7200)
        self._token_expire_at = time.time() + expire
        logger.info(f"[Meegle] Token 获取成功，有效期 {expire} 秒")
        return self._token

    def _headers(self) -> Dict:
        return {
            "Content-Type": "application/json",
            "X-Plugin-Token": self._get_token(),
            "X-User-Key": self.user_key
        }

    def _post(self, endpoint: str, payload: Optional[dict] = None) -> dict:
        """POST 请求，含重试"""
        url = f"{self.base_url}{endpoint}"
        for attempt in range(3):
            try:
                resp = requests.post(url, headers=self._headers(), json=payload or {}, timeout=20)
                resp.raise_for_status()
                data = resp.json()
                err_code = data.get("err_code", data.get("error", {}).get("code", -1))
                if err_code == 0:
                    return data
                err_msg = data.get("err_msg", data.get("error", {}).get("msg", "未知错误"))
                if err_code in [10301, 10022, 20039, 9999]:
                    raise Exception(f"[Meegle] 不可重试错误: code={err_code}, msg={err_msg}")
                logger.warning(f"[Meegle] POST {endpoint} 第{attempt+1}/3次失败: {err_code} {err_msg}")
            except requests.exceptions.RequestException as e:
                logger.warning(f"[Meegle] POST 请求异常 第{attempt+1}/3次: {e}")
            if attempt < 2:
                time.sleep(0.5 * (2 ** attempt))
        raise Exception(f"[Meegle] POST {endpoint} 在3次重试后失败")

    def _get(self, endpoint: str, params: Optional[dict] = None) -> dict:
        """GET 请求，含重试"""
        url = f"{self.base_url}{endpoint}"
        for attempt in range(3):
            try:
                resp = requests.get(url, headers=self._headers(), params=params, timeout=20)
                resp.raise_for_status()
                data = resp.json()
                err_code = data.get("err_code", data.get("error", {}).get("code", -1))
                if err_code == 0:
                    return data
                err_msg = data.get("err_msg", data.get("error", {}).get("msg", "未知错误"))
                if err_code in [10301, 10022, 20039, 9999]:
                    raise Exception(f"[Meegle] 不可重试错误: code={err_code}, msg={err_msg}")
                logger.warning(f"[Meegle] GET {endpoint} 第{attempt+1}/3次失败: {err_code} {err_msg}")
            except requests.exceptions.RequestException as e:
                logger.warning(f"[Meegle] GET 请求异常 第{attempt+1}/3次: {e}")
            if attempt < 2:
                time.sleep(0.5 * (2 ** attempt))
        raise Exception(f"[Meegle] GET {endpoint} 在3次重试后失败")

    # ---- 工作项类型 ----

    def get_work_item_types(self, project_key: str) -> List[Dict]:
        """获取空间内所有工作项类型"""
        data = self._get(f"/{project_key}/work_item/all-types")
        return data.get("data", [])

    # ---- 工作项过滤/列表 ----

    def filter_work_items(self, project_key: str, work_item_type_keys: List[str],
                          page_num: int = 1, page_size: int = 50) -> Dict:
        """
        分页获取工作项列表（含完整字段）

        :param project_key: 项目 Key
        :param work_item_type_keys: 工作项类型 Key 列表
        :param page_num: 页码（从 1 开始）
        :param page_size: 每页数量（最大 50）
        :return: {"data": [...], "pagination": {"total": N, ...}}
        """
        payload = {
            "work_item_type_keys": work_item_type_keys,
            "page_num": page_num,
            "page_size": min(page_size, 50)
        }
        return self._post(f"/{project_key}/work_item/filter", payload)

    def fetch_all_work_items(self, project_key: str, work_item_type_key: str,
                             page_size: int = 50) -> List[Dict]:
        """
        获取指定类型的所有工作项（自动分页）

        :param project_key: 项目 Key
        :param work_item_type_key: 工作项类型 Key（如 "issue", "sub_task"）
        :param page_size: 每页数量
        :return: 所有工作项列表
        """
        all_items = []
        page_num = 1

        while True:
            result = self.filter_work_items(project_key, [work_item_type_key], page_num, page_size)
            items = result.get("data", [])
            pagination = result.get("pagination", {})
            total = pagination.get("total", 0)

            all_items.extend(items)
            logger.info(f"[Meegle] {work_item_type_key} 第{page_num}页: {len(items)}条，累计 {len(all_items)}/{total}")

            if len(all_items) >= total or not items:
                break
            page_num += 1
            time.sleep(0.3)

        return all_items

    # ---- 用户查询 ----

    def query_users(self, user_keys: List[str]) -> List[Dict]:
        """
        批量查询用户信息（通过 user_key 列表）

        注意：/user/query 接口需要传入 user_keys 参数，
        经测试 virtual_token 下仅能查到插件 master 自身的信息。
        其他用户信息将以 user_key 原值作为名称显示。

        :param user_keys: 用户 Key 列表
        :return: 用户信息列表，每项含 user_key, name, email
        """
        if not user_keys:
            return []
        try:
            data = self._post("/user/query", {"user_keys": user_keys})
            return data.get("data", [])
        except Exception as e:
            logger.warning(f"[Meegle] /user/query 失败（将使用 user_key 原値）: {e}")
            return []

    def list_work_items_by_week(
        self,
        module_label: str,
        week_start: str,
        week_end: str,
        project_key: Optional[str] = None,
    ) -> Dict[str, int]:
        """
        统计指定模块标签在指定周内完成的 Story 数量和新增的 Defect 数量。
        Meegle API 返回的时间戳是毫秒级，状态在 work_item_status 对象中，标签在 fields 数组中。
        :param module_label: 模块名称简称（用于匹配工作项标签或名称）
        :param week_start: 周开始日期（YYYY-MM-DD）
        :param week_end: 周结束日期（YYYY-MM-DD）
        :return: {"completed_stories": N, "new_defects": N, "resolved_defects": N}
        """
        import datetime
        pk = project_key or (self.project_key if hasattr(self, 'project_key') else "42nqu9")

        def _date_to_ms(date_str: str, end_of_day: bool = False) -> int:
            """Meegle 时间戳为毫秒级"""
            dt = datetime.datetime.strptime(date_str, "%Y-%m-%d")
            if end_of_day:
                dt = dt.replace(hour=23, minute=59, second=59)
            return int(dt.timestamp() * 1000)

        def _get_field(item: dict, field_key: str):
            """Meegle 工作项字段在 fields 数组中"""
            for f in item.get("fields", []):
                if f.get("field_key") == field_key or f.get("field_alias") == field_key:
                    return f.get("field_value")
            return None

        def _is_done(item: dict) -> bool:
            """Story 是否已完成"""
            # 方式1： finish_status 字段
            finish_status = _get_field(item, "finish_status")
            if finish_status is True:
                return True
            # 方式2： work_item_status.state_category
            status_obj = item.get("work_item_status", {})
            if isinstance(status_obj, dict):
                cat = status_obj.get("state_category", "")
                if cat in ["DONE", "CLOSED", "done", "closed"]:
                    return True
                name = status_obj.get("name", "")
                if name in ["已完成", "已关闭", "已上线"]:
                    return True
            return False

        def _is_resolved(item: dict) -> bool:
            """Defect 是否已修复"""
            status_obj = item.get("work_item_status", {})
            if isinstance(status_obj, dict):
                cat = status_obj.get("state_category", "")
                if cat in ["DONE", "CLOSED", "done", "closed"]:
                    return True
                name = status_obj.get("name", "")
                if name in ["已修复", "已关闭", "已验证"]:
                    return True
            return False

        def _get_tags(item: dict) -> str:
            """Meegle 标签在 fields 中的 tags 字段"""
            tags_val = _get_field(item, "tags")
            if isinstance(tags_val, list):
                return " ".join(t.get("label", "") for t in tags_val if isinstance(t, dict))
            return ""

        start_ms = _date_to_ms(week_start)
        end_ms = _date_to_ms(week_end, end_of_day=True)

        completed_stories = 0
        new_defects = 0
        resolved_defects = 0

        try:
            stories = self.fetch_all_work_items(pk, "story")
            for item in stories:
                item_name = item.get("name", "")
                tag_str = _get_tags(item)
                search_str = tag_str + " " + item_name
                if module_label not in search_str:
                    continue
                updated_at = item.get("updated_at", 0)  # 毫秒
                if _is_done(item) and start_ms <= updated_at <= end_ms:
                    completed_stories += 1
        except Exception as e:
            logger.warning(f"[Meegle] 获取 Story 失败: {e}")

        try:
            issues = self.fetch_all_work_items(pk, "issue")
            for item in issues:
                item_name = item.get("name", "")
                tag_str = _get_tags(item)
                search_str = tag_str + " " + item_name
                if module_label not in search_str:
                    continue
                created_at = item.get("created_at", 0)  # 毫秒
                if start_ms <= created_at <= end_ms:
                    new_defects += 1
                updated_at = item.get("updated_at", 0)
                if _is_resolved(item) and start_ms <= updated_at <= end_ms:
                    resolved_defects += 1
        except Exception as e:
            logger.warning(f"[Meegle] 获取 Defect 失败: {e}")

        logger.info(
            f"[Meegle] 模块={module_label} 周={week_start}~{week_end}: "
            f"story={completed_stories} defect+{new_defects}/-{resolved_defects}"
        )
        return {
            "completed_stories": completed_stories,
            "new_defects": new_defects,
            "resolved_defects": resolved_defects,
        }

