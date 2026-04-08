/**
 * DataContext - 全局数据 Context
 * XPBET 全球站功能地图管理系统
 *
 * 管理飞书 Bitable 数据的拉取、转换、过滤和状态。
 * 提供全局数据访问和操作方法。
 */

import React, {
  createContext,
  useContext,
  useReducer,
  useCallback,
  useEffect,
  type ReactNode,
} from 'react';
import { message } from 'antd';
import { fetchAllBitableData } from '../services/feishuApi';
import {
  transformToMindMap,
  filterMindMap,
  type MindMapRoot,
  type FilterOptions,
} from '../services/transformer';

// ==================== 状态类型定义 ====================

interface DataState {
  /** 完整的原始树形数据（未过滤） */
  rawData: MindMapRoot | null;
  /** 经过过滤的树形数据（用于渲染） */
  filteredData: MindMapRoot | null;
  /** 当前过滤条件 */
  filters: FilterOptions;
  /** 加载状态 */
  loading: boolean;
  /** 错误信息 */
  error: string | null;
  /** 最后同步时间 */
  lastSyncedAt: Date | null;
}

// ==================== Action 类型定义 ====================

type DataAction =
  | { type: 'FETCH_START' }
  | { type: 'FETCH_SUCCESS'; payload: MindMapRoot }
  | { type: 'FETCH_ERROR'; payload: string }
  | { type: 'SET_FILTERS'; payload: FilterOptions };

// ==================== Reducer ====================

function dataReducer(state: DataState, action: DataAction): DataState {
  switch (action.type) {
    case 'FETCH_START':
      return { ...state, loading: true, error: null };

    case 'FETCH_SUCCESS':
      return {
        ...state,
        loading: false,
        rawData: action.payload,
        filteredData: filterMindMap(action.payload, state.filters),
        lastSyncedAt: new Date(),
        error: null,
      };

    case 'FETCH_ERROR':
      return { ...state, loading: false, error: action.payload };

    case 'SET_FILTERS':
      return {
        ...state,
        filters: action.payload,
        filteredData: state.rawData
          ? filterMindMap(state.rawData, action.payload)
          : null,
      };

    default:
      return state;
  }
}

// ==================== 初始状态 ====================

const initialState: DataState = {
  rawData: null,
  filteredData: null,
  filters: {},
  loading: false,
  error: null,
  lastSyncedAt: null,
};

// ==================== Context 定义 ====================

interface DataContextValue extends DataState {
  /** 拉取飞书数据并更新状态 */
  fetchData: () => Promise<void>;
  /** 更新过滤条件 */
  setFilters: (filters: FilterOptions) => void;
  /** 清除所有过滤条件 */
  clearFilters: () => void;
}

const DataContext = createContext<DataContextValue | null>(null);

// ==================== Provider 组件 ====================

interface DataProviderProps {
  children: ReactNode;
  /** 飞书应用 App ID */
  appId: string;
  /** 飞书应用 App Secret */
  appSecret: string;
}

export const DataProvider: React.FC<DataProviderProps> = ({
  children,
  appId,
  appSecret,
}) => {
  const [state, dispatch] = useReducer(dataReducer, initialState);

  const fetchData = useCallback(async () => {
    dispatch({ type: 'FETCH_START' });

    try {
      const { modules, features } = await fetchAllBitableData(appId, appSecret);
      const mindMapData = transformToMindMap(modules, features);
      dispatch({ type: 'FETCH_SUCCESS', payload: mindMapData });
      message.success(`数据加载完成：${modules.length} 个模块，${features.length} 个功能`);
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : '数据加载失败，请检查网络或飞书 API 配置';
      dispatch({ type: 'FETCH_ERROR', payload: errorMessage });
      message.error(errorMessage);
    }
  }, [appId, appSecret]);

  const setFilters = useCallback((filters: FilterOptions) => {
    dispatch({ type: 'SET_FILTERS', payload: filters });
  }, []);

  const clearFilters = useCallback(() => {
    dispatch({ type: 'SET_FILTERS', payload: {} });
  }, []);

  // 组件挂载时自动拉取数据
  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const value: DataContextValue = {
    ...state,
    fetchData,
    setFilters,
    clearFilters,
  };

  return <DataContext.Provider value={value}>{children}</DataContext.Provider>;
};

// ==================== Hook ====================

/**
 * 使用全局数据 Context
 * 必须在 DataProvider 内部使用
 */
export function useData(): DataContextValue {
  const context = useContext(DataContext);
  if (!context) {
    throw new Error('useData 必须在 DataProvider 内部使用');
  }
  return context;
}
