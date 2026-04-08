/**
 * useBitableData.ts - 飞书 Bitable 数据加载 Hook
 * XPBET 全球站功能地图管理系统
 *
 * 功能：
 * 1. 根据环境变量 VITE_USE_STATIC_DATA 决定使用飞书 API 还是静态 JSON
 * 2. 管理加载状态（loading）、错误状态（error）和数据状态（data）
 * 3. 支持手动刷新（refetch）
 * 4. API 失败时自动降级到静态 JSON fallback
 *
 * 环境变量配置：
 * - VITE_USE_STATIC_DATA=true    使用静态 JSON（开发/演示模式）
 * - VITE_FEISHU_APP_ID=xxx       飞书应用 App ID
 * - VITE_FEISHU_APP_SECRET=xxx   飞书应用 App Secret
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import type { MindMapRoot } from '../types/mindmap';
import { fetchAllBitableData } from '../services/biTableService';
import { transformToMindMap } from './dataTransformer';

// ==================== 类型定义 ====================

export interface UseBitableDataResult {
  /** 加载状态 */
  loading: boolean;
  /** 错误信息（null 表示无错误） */
  error: string | null;
  /** 加载成功的 MindMap 数据（null 表示尚未加载） */
  data: MindMapRoot | null;
  /** 最后同步时间 */
  lastSyncedAt: Date | null;
  /** 数据来源（'api' | 'static' | 'fallback'） */
  dataSource: 'api' | 'static' | 'fallback' | null;
  /** 手动触发重新拉取数据 */
  refetch: () => void;
}

// ==================== 环境变量读取 ====================

/**
 * 读取环境变量配置
 * Vite 通过 import.meta.env 暴露 VITE_ 前缀的环境变量
 */
function getEnvConfig() {
  return {
    useStaticData: import.meta.env.VITE_USE_STATIC_DATA === 'true',
    appId: import.meta.env.VITE_FEISHU_APP_ID as string | undefined,
    appSecret: import.meta.env.VITE_FEISHU_APP_SECRET as string | undefined,
  };
}

// ==================== Hook 实现 ====================

/**
 * 飞书 Bitable 数据加载 Hook
 *
 * 使用示例：
 * ```tsx
 * const { loading, error, data, refetch } = useBitableData();
 *
 * if (loading) return <LoadingSpinner />;
 * if (error) return <ErrorPanel message={error} onRetry={refetch} />;
 * if (!data) return null;
 * return <MindMapCanvas data={data} />;
 * ```
 */
export function useBitableData(): UseBitableDataResult {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<MindMapRoot | null>(null);
  const [lastSyncedAt, setLastSyncedAt] = useState<Date | null>(null);
  const [dataSource, setDataSource] = useState<UseBitableDataResult['dataSource']>(null);

  // 使用 ref 避免重复请求
  const isFetchingRef = useRef(false);

  const fetchData = useCallback(async () => {
    if (isFetchingRef.current) return;
    isFetchingRef.current = true;

    setLoading(true);
    setError(null);

    const { useStaticData, appId, appSecret } = getEnvConfig();

    try {
      // ── 模式 1: 静态 JSON 模式（VITE_USE_STATIC_DATA=true）──────────
      if (useStaticData) {
        console.log('[useBitableData] 使用静态 JSON 数据（VITE_USE_STATIC_DATA=true）');
        const staticModule = await import('../data/mindmap_data.json');
        const staticData = staticModule.default as MindMapRoot;
        setData(staticData);
        setDataSource('static');
        setLastSyncedAt(new Date());
        setLoading(false);
        isFetchingRef.current = false;
        return;
      }

      // ── 模式 2: 飞书 API 模式 ────────────────────────────────────────
      if (!appId || !appSecret) {
        throw new Error(
          '飞书 API 配置缺失：请在 .env 文件中设置 VITE_FEISHU_APP_ID 和 VITE_FEISHU_APP_SECRET'
        );
      }

      console.log('[useBitableData] 从飞书 Bitable API 拉取数据...');
      const { modules, features } = await fetchAllBitableData(appId, appSecret);
      const mindMapData = transformToMindMap(modules, features);

      setData(mindMapData);
      setDataSource('api');
      setLastSyncedAt(new Date());
      setError(null);

      console.log(
        `[useBitableData] 数据加载完成: ${modules.length} 个模块, ${features.length} 个功能`
      );
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : '数据加载失败，请检查网络或飞书 API 配置';

      console.error('[useBitableData] 数据加载失败:', err);

      // ── 降级策略: API 失败时尝试加载静态 JSON ──────────────────────
      try {
        console.warn('[useBitableData] API 失败，尝试加载静态 JSON fallback...');
        const staticModule = await import('../data/mindmap_data.json');
        const staticData = staticModule.default as MindMapRoot;
        setData(staticData);
        setDataSource('fallback');
        setLastSyncedAt(new Date());
        setError(`API 不可用（${errorMessage}），已加载本地缓存数据`);
      } catch {
        // 静态 JSON 也加载失败
        setError(errorMessage);
        setData(null);
        setDataSource(null);
      }
    } finally {
      setLoading(false);
      isFetchingRef.current = false;
    }
  }, []);

  // 组件挂载时自动拉取数据
  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return {
    loading,
    error,
    data,
    lastSyncedAt,
    dataSource,
    refetch: fetchData,
  };
}
