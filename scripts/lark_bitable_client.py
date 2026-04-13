import os
import requests
from typing import Dict, List, Optional, Any

class LarkBitableClient:
    """
    通用 Lark (Feishu) Bitable 客户端，提供多维表格的 CRUD 能力。
    凭证信息通过环境变量读取。
    """
    
    def __init__(self, app_id: Optional[str] = None, app_secret: Optional[str] = None):
        self.app_id = app_id or os.environ.get("LARK_APP_ID")
        self.app_secret = app_secret or os.environ.get("LARK_APP_SECRET")
        
        if not self.app_id or not self.app_secret:
            raise ValueError("LARK_APP_ID and LARK_APP_SECRET must be provided or set in environment variables.")
            
        self.tenant_access_token = None
        self._refresh_token()

    def _refresh_token(self) -> None:
        """获取或刷新 tenant_access_token"""
        url = "https://open.larksuite.com/open-apis/auth/v3/tenant_access_token/internal"
        payload = {
            "app_id": self.app_id,
            "app_secret": self.app_secret
        }
        response = requests.post(url, json=payload)
        response.raise_for_status()
        data = response.json()
        
        if data.get("code") != 0:
            raise Exception(f"Failed to get token: {data.get('msg')}")
            
        self.tenant_access_token = data.get("tenant_access_token")

    def _get_headers(self) -> Dict[str, str]:
        if not self.tenant_access_token:
            self._refresh_token()
        return {
            "Authorization": f"Bearer {self.tenant_access_token}",
            "Content-Type": "application/json"
        }

    def list_records(self, base_id: str, table_id: str, page_size: int = 500, filter_str: str = "") -> List[Dict]:
        """列出表格中的记录"""
        url = f"https://open.larksuite.com/open-apis/bitable/v1/apps/{base_id}/tables/{table_id}/records"
        params = {"page_size": page_size}
        if filter_str:
            params["filter"] = filter_str
            
        all_records = []
        page_token = ""
        
        while True:
            if page_token:
                params["page_token"] = page_token
                
            response = requests.get(url, headers=self._get_headers(), params=params)
            response.raise_for_status()
            data = response.json().get("data", {})
            
            items = data.get("items", [])
            if items:
                all_records.extend(items)
                
            if data.get("has_more"):
                page_token = data.get("page_token")
            else:
                break
                
        return all_records

    def create_record(self, base_id: str, table_id: str, fields: Dict[str, Any]) -> Dict:
        """创建一条新记录"""
        url = f"https://open.larksuite.com/open-apis/bitable/v1/apps/{base_id}/tables/{table_id}/records"
        payload = {"fields": fields}
        
        response = requests.post(url, headers=self._get_headers(), json=payload)
        response.raise_for_status()
        return response.json().get("data", {}).get("record", {})

    def update_record(self, base_id: str, table_id: str, record_id: str, fields: Dict[str, Any]) -> Dict:
        """更新一条记录"""
        url = f"https://open.larksuite.com/open-apis/bitable/v1/apps/{base_id}/tables/{table_id}/records/{record_id}"
        payload = {"fields": fields}
        
        response = requests.put(url, headers=self._get_headers(), json=payload)
        response.raise_for_status()
        return response.json().get("data", {}).get("record", {})

    def delete_record(self, base_id: str, table_id: str, record_id: str) -> bool:
        """删除一条记录"""
        url = f"https://open.larksuite.com/open-apis/bitable/v1/apps/{base_id}/tables/{table_id}/records/{record_id}"
        
        response = requests.delete(url, headers=self._get_headers())
        response.raise_for_status()
        return response.json().get("code") == 0
