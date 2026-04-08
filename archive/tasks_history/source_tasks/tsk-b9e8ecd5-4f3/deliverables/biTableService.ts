/**
 * biTableService.ts - 飞书 Bitable API 数据层
 * XPBET 全球站功能地图管理系统
 *
 * 功能：
 * 1. 获取飞书 tenant_access_token（内存缓存，避免重复请求）
 * 2. 并发拉取模块表和功能表全量数据（自动处理分页）
 * 3. 支持通过环境变量 VITE_USE_STATIC_DATA=true 切换为静态 JSON fallback
 *
 * 飞书 API 文档: https://open.feishu.cn/document/server-docs/docs/bitable-v1/bitable-overview
 */

// ==================== 配置常量 ====================

/**
 * 飞书多维表格数据源配置
 * BASE_ID 和 TABLE_ID 来自新版多维表格搭建结果 (tsk-291891b6-9ce)
 * 访问链接: https://kjpp4yydjn38.jp.larksuite.com/base/BgjjbdZiJanHTpsboAzj9Gv7p6b
 * 数据规模: 21 个模块, 114 个功能
 */
export const BITABLE_CONFIG = {
  /**
   * 多维表格 Base ID
   * 来源: tsk-291891b6-9ce 新版多维表格搭建结果
   */
  BASE_ID: 'BgjjbdZiJanHTpsboAzj9Gv7p6b',
  /** 模块表 Table ID（21 个模块） */
  MODULE_TABLE_ID: 'tblb9Owa8P4AhVEH',
  /** 功能表 Table ID（114 个功能） */
  FEATURE_TABLE_ID: 'tbluOwbl2PKxIiEz',
  /** 飞书 API 基础 URL */
  API_BASE_URL: 'https://open.feishu.cn/open-apis',
  /** 每页最大记录数（飞书 API 上限） */
  PAGE_SIZE: 500,
} as const;

// ==================== 类型定义 ====================

/** 飞书 API 通用响应结构 */
interface FeishuApiResponse<T> {
  code: number;
  msg: string;
  data: T;
}

/** 飞书 tenant_access_token 响应 */
interface TenantTokenResponse {
  code: number;
  msg: string;
  tenant_access_token: string;
  expire: number;
}

/** 飞书多维表格记录 */
export interface BitableRecord {
  record_id: string;
  fields: Record<string, unknown>;
}

/** 飞书多维表格记录列表响应 */
interface BitableRecordsResponse {
  items: BitableRecord[];
  page_token: string;
  has_more: boolean;
  total: number;
}

/** 模块表原始字段类型定义 */
export interface ModuleFields {
  /** 模块名称（文本字段） */
  模块名称: string;
  /** 分类（单选字段，可能是字符串或 { text: string } 对象） */
  分类: string | { text: string };
  /** 优先级（单选字段） */
  优先级: string | { text: string };
  /** 状态（单选字段） */
  状态: string | { text: string };
  /** 负责人（人员字段，数组格式） */
  负责人?: Array<{ id: string; name: string; en_name: string; email: string }>;
  /** 模块说明（文本字段） */
  模块说明?: string;
  /** 包含功能（关联字段） */
  包含功能?: Array<{ record_id: string; table_id: string; text?: string }>;
}

/** 功能表原始字段类型定义 */
export interface FeatureFields {
  /** 功能名称（文本字段） */
  功能名称: string;
  /** 功能说明（文本字段） */
  功能说明?: string;
  /** 状态（单选字段） */
  状态?: string | { text: string };
  /** 功能优先级（单选字段） */
  功能优先级?: string | { text: string };
  /** 阶段（单选字段） */
  阶段?: string | { text: string };
  /** 迭代版本（单选字段） */
  迭代版本?: string | { text: string };
  /**
   * 所属模块（关联字段）
   * 注意：飞书关联字段格式为 [{ record_ids: ["recXXX"], table_id: "...", text: "..." }]
   * 或旧格式 [{ record_id: "recXXX", table_id: "..." }]
   */
  所属模块?: Array<{
    record_id?: string;
    record_ids?: string[];
    table_id: string;
    text?: string;
  }>;
  /** 负责人（人员字段，可能是数组或 { users: [...] } 对象） */
  负责人?: Array<{ id: string; name: string; en_name: string; email: string }>
    | { users: Array<{ id: string; name: string; en_name: string; email: string }> };
  /** 文档链接（超链接字段） */
  文档链接?: { link: string; text: string } | string;
  /** 简化方案（文本字段） */
  简化方案?: string;
  /** 前置资源（文本字段） */
  前置资源?: string;
}

/** fetchAllBitableData 返回值 */
export interface BitableData {
  modules: BitableRecord[];
  features: BitableRecord[];
}

// ==================== Token 缓存管理 ====================

/** Token 内存缓存（页面刷新后重新获取） */
let tokenCache: { token: string; expireAt: number } | null = null;

/**
 * 获取飞书 tenant_access_token
 * 支持内存缓存，提前 60 秒过期以防边界情况
 *
 * @param appId 飞书应用 App ID（来自环境变量 VITE_FEISHU_APP_ID）
 * @param appSecret 飞书应用 App Secret（来自环境变量 VITE_FEISHU_APP_SECRET）
 * @returns tenant_access_token 字符串
 * @throws 获取失败时抛出包含错误信息的 Error
 */
export async function getTenantAccessToken(appId: string, appSecret: string): Promise<string> {
  // 检查缓存是否有效（提前 60 秒过期）
  if (tokenCache && Date.now() < tokenCache.expireAt - 60_000) {
    return tokenCache.token;
  }

  const response = await fetch(
    `${BITABLE_CONFIG.API_BASE_URL}/auth/v3/tenant_access_token/internal`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ app_id: appId, app_secret: appSecret }),
    }
  );

  if (!response.ok) {
    throw new Error(`飞书 Token 请求失败: HTTP ${response.status}`);
  }

  const data: TenantTokenResponse = await response.json();

  if (data.code !== 0) {
    throw new Error(`获取飞书 Token 失败 (code=${data.code}): ${data.msg}`);
  }

  tokenCache = {
    token: data.tenant_access_token,
    expireAt: Date.now() + data.expire * 1000,
  };

  return tokenCache.token;
}

/**
 * 清除 Token 缓存（用于强制刷新或登出场景）
 */
export function clearTokenCache(): void {
  tokenCache = null;
}

// ==================== 多维表格 API ====================

/**
 * 获取多维表格全量记录（自动处理分页）
 *
 * @param token tenant_access_token
 * @param tableId 表格 ID
 * @returns 所有记录数组
 */
async function fetchAllRecords(token: string, tableId: string): Promise<BitableRecord[]> {
  const allRecords: BitableRecord[] = [];
  let pageToken: string | undefined;
  let hasMore = true;

  while (hasMore) {
    const url = new URL(
      `${BITABLE_CONFIG.API_BASE_URL}/bitable/v1/apps/${BITABLE_CONFIG.BASE_ID}/tables/${tableId}/records`
    );
    url.searchParams.set('page_size', String(BITABLE_CONFIG.PAGE_SIZE));
    if (pageToken) {
      url.searchParams.set('page_token', pageToken);
    }

    const response = await fetch(url.toString(), {
      headers: {
        Authorization: `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error(`获取多维表格记录失败: HTTP ${response.status} (tableId: ${tableId})`);
    }

    const json: FeishuApiResponse<BitableRecordsResponse> = await response.json();

    if (json.code !== 0) {
      throw new Error(`飞书 API 错误 (code=${json.code}): ${json.msg} (tableId: ${tableId})`);
    }

    const { items, page_token, has_more } = json.data;
    allRecords.push(...items);
    pageToken = page_token;
    hasMore = has_more;
  }

  return allRecords;
}

// ==================== 主要导出函数 ====================

/**
 * 获取模块表全量数据
 *
 * @param token tenant_access_token
 * @returns 模块表记录数组（含 record_id 和 fields）
 */
export async function fetchModuleRecords(token: string): Promise<BitableRecord[]> {
  return fetchAllRecords(token, BITABLE_CONFIG.MODULE_TABLE_ID);
}

/**
 * 获取功能表全量数据
 *
 * @param token tenant_access_token
 * @returns 功能表记录数组（含 record_id 和 fields）
 */
export async function fetchFeatureRecords(token: string): Promise<BitableRecord[]> {
  return fetchAllRecords(token, BITABLE_CONFIG.FEATURE_TABLE_ID);
}

/**
 * 并发获取模块表和功能表全量数据
 *
 * 使用 Promise.all 并发拉取两张表，相比串行拉取可减少约 50% 的等待时间。
 *
 * @param appId 飞书应用 App ID（来自环境变量 VITE_FEISHU_APP_ID）
 * @param appSecret 飞书应用 App Secret（来自环境变量 VITE_FEISHU_APP_SECRET）
 * @returns { modules, features } 原始记录数组
 * @throws 网络错误或飞书 API 错误时抛出 Error
 */
export async function fetchAllBitableData(
  appId: string,
  appSecret: string
): Promise<BitableData> {
  // Step 1: 获取访问令牌
  const token = await getTenantAccessToken(appId, appSecret);

  // Step 2: 并发拉取两张表（提升加载速度）
  const [modules, features] = await Promise.all([
    fetchModuleRecords(token),
    fetchFeatureRecords(token),
  ]);

  console.log(
    `[BiTableService] 数据加载完成: ${modules.length} 个模块, ${features.length} 个功能`
  );

  return { modules, features };
}
