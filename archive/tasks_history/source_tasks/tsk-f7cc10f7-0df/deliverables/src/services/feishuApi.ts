/**
 * 飞书 Bitable API 调用封装
 * XPBET 全球站功能地图管理系统
 *
 * 飞书 API 文档: https://open.feishu.cn/document/server-docs/docs/bitable-v1/bitable-overview
 */

import axios, { AxiosInstance } from 'axios';

// ==================== 配置常量 ====================

/** 飞书多维表格数据源配置（来自数据结构设计文档） */
export const FEISHU_CONFIG = {
  /** 多维表格 Base ID */
  BASE_ID: 'CyDxbUQGGa3N2NsVanMjqdjxp6e',
  /** 模块表 Table ID */
  MODULE_TABLE_ID: 'tblaDW4D2hQS2xCw',
  /** 功能表 Table ID */
  FEATURE_TABLE_ID: 'tblLzX7wqGWFr9KP',
  /** 飞书 API 基础 URL */
  API_BASE_URL: 'https://open.feishu.cn/open-apis',
  /** 每页最大记录数 */
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

/** 模块表原始字段 */
export interface ModuleFields {
  模块名称: string;
  分类: string;
  优先级: string;
  状态: string;
  负责人?: Array<{ id: string; name: string; en_name: string; email: string }>;
  模块说明?: string;
  包含功能?: Array<{ record_id: string; table_id: string }>;
}

/** 功能表原始字段 */
export interface FeatureFields {
  功能名称: string;
  功能说明?: string;
  状态?: string;
  功能优先级?: string;
  阶段?: string;
  迭代版本?: string;
  所属模块?: Array<{ record_id: string; table_id: string }>;
  负责人?: Array<{ id: string; name: string; en_name: string; email: string }>;
  文档链接?: { link: string; text: string };
  简化方案?: string;
  前置资源?: string;
}

// ==================== Token 管理 ====================

/** Token 缓存（内存缓存，页面刷新后重新获取） */
let cachedToken: { token: string; expireAt: number } | null = null;

/**
 * 获取飞书 tenant_access_token
 * 支持内存缓存，避免频繁请求
 *
 * @param appId 飞书应用 App ID
 * @param appSecret 飞书应用 App Secret
 * @returns tenant_access_token
 */
export async function getTenantAccessToken(appId: string, appSecret: string): Promise<string> {
  // 检查缓存是否有效（提前 60 秒过期以防边界情况）
  if (cachedToken && Date.now() < cachedToken.expireAt - 60_000) {
    return cachedToken.token;
  }

  const response = await axios.post<TenantTokenResponse>(
    `${FEISHU_CONFIG.API_BASE_URL}/auth/v3/tenant_access_token/internal`,
    { app_id: appId, app_secret: appSecret },
    { headers: { 'Content-Type': 'application/json' } }
  );

  if (response.data.code !== 0) {
    throw new Error(`获取飞书 Token 失败: ${response.data.msg}`);
  }

  cachedToken = {
    token: response.data.tenant_access_token,
    expireAt: Date.now() + response.data.expire * 1000,
  };

  return cachedToken.token;
}

// ==================== API 客户端工厂 ====================

/**
 * 创建已配置鉴权的飞书 API Axios 实例
 *
 * @param token tenant_access_token
 * @returns 配置好的 Axios 实例
 */
function createFeishuClient(token: string): AxiosInstance {
  return axios.create({
    baseURL: FEISHU_CONFIG.API_BASE_URL,
    headers: {
      Authorization: `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    timeout: 10_000,
  });
}

// ==================== 多维表格 API ====================

/**
 * 获取多维表格全量记录（自动处理分页）
 *
 * @param client 飞书 API 客户端
 * @param tableId 表格 ID
 * @returns 所有记录数组
 */
async function fetchAllRecords(
  client: AxiosInstance,
  tableId: string
): Promise<BitableRecord[]> {
  const allRecords: BitableRecord[] = [];
  let pageToken: string | undefined;
  let hasMore = true;

  while (hasMore) {
    const params: Record<string, unknown> = {
      page_size: FEISHU_CONFIG.PAGE_SIZE,
    };
    if (pageToken) {
      params.page_token = pageToken;
    }

    const response = await client.get<FeishuApiResponse<BitableRecordsResponse>>(
      `/bitable/v1/apps/${FEISHU_CONFIG.BASE_ID}/tables/${tableId}/records`,
      { params }
    );

    if (response.data.code !== 0) {
      throw new Error(`获取多维表格记录失败: ${response.data.msg}`);
    }

    const { items, page_token, has_more } = response.data.data;
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
export async function fetchModuleRecords(
  token: string
): Promise<BitableRecord[]> {
  const client = createFeishuClient(token);
  return fetchAllRecords(client, FEISHU_CONFIG.MODULE_TABLE_ID);
}

/**
 * 获取功能表全量数据
 *
 * @param token tenant_access_token
 * @returns 功能表记录数组（含 record_id 和 fields）
 */
export async function fetchFeatureRecords(
  token: string
): Promise<BitableRecord[]> {
  const client = createFeishuClient(token);
  return fetchAllRecords(client, FEISHU_CONFIG.FEATURE_TABLE_ID);
}

/**
 * 并发获取模块表和功能表全量数据
 *
 * @param appId 飞书应用 App ID
 * @param appSecret 飞书应用 App Secret
 * @returns { modules, features } 原始记录数组
 */
export async function fetchAllBitableData(
  appId: string,
  appSecret: string
): Promise<{ modules: BitableRecord[]; features: BitableRecord[] }> {
  const token = await getTenantAccessToken(appId, appSecret);

  // 并发拉取两张表，提升加载速度
  const [modules, features] = await Promise.all([
    fetchModuleRecords(token),
    fetchFeatureRecords(token),
  ]);

  console.log(`[FeishuAPI] 数据加载完成: ${modules.length} 个模块, ${features.length} 个功能`);

  return { modules, features };
}
