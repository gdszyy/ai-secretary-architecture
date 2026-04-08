/**
 * ControlPanel - 控制面板主组件
 * XPBET 全球站功能地图管理系统
 *
 * 提供搜索、过滤和视图切换功能，通过 DataContext 与数据层通信。
 */

import React, { useState, useCallback } from 'react';
import { Input, Select, Button, Space, Tooltip, Badge } from 'antd';
import {
  SearchOutlined,
  FilterOutlined,
  ReloadOutlined,
  FullscreenOutlined,
  AppstoreOutlined,
  MenuOutlined,
} from '@ant-design/icons';
import type { FilterOptions } from '../../services/transformer';

const { Option } = Select;

// ==================== 常量 ====================

const STATUS_OPTIONS = ['完成', '测试中', '开发中', '待技术评审', '待需求评审', '规划中', '待规划'];
const PRIORITY_OPTIONS = ['P0', 'P1', 'P2', 'P3'];
const STAGE_OPTIONS = ['1月SR验证', '3月基础上线', '6月后续迭代', '6月迭代'];
const CATEGORY_OPTIONS = ['T0基础框架', 'T1营销框架-获客', 'T1营销框架-运营', 'T1营销框架-数据分析', 'T2商户管理'];

// ==================== 类型定义 ====================

interface ControlPanelProps {
  /** 当前过滤条件 */
  filters: FilterOptions;
  /** 过滤条件变化回调 */
  onFiltersChange: (filters: FilterOptions) => void;
  /** 当前视图方向 */
  direction: 'H' | 'V';
  /** 视图方向变化回调 */
  onDirectionChange: (direction: 'H' | 'V') => void;
  /** 刷新数据回调 */
  onRefresh: () => void;
  /** 是否正在加载 */
  loading?: boolean;
  /** 当前显示的节点数量（过滤后） */
  filteredCount?: number;
  /** 总节点数量 */
  totalCount?: number;
}

// ==================== 组件 ====================

export const ControlPanel: React.FC<ControlPanelProps> = ({
  filters,
  onFiltersChange,
  direction,
  onDirectionChange,
  onRefresh,
  loading = false,
  filteredCount,
  totalCount,
}) => {
  const [showAdvancedFilters, setShowAdvancedFilters] = useState(false);

  // 计算活跃过滤器数量（用于 Badge 展示）
  const activeFilterCount = [
    filters.keyword,
    ...(filters.statuses ?? []),
    ...(filters.priorities ?? []),
    ...(filters.stages ?? []),
    filters.owner,
    filters.category,
  ].filter(Boolean).length;

  const handleKeywordChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      onFiltersChange({ ...filters, keyword: e.target.value });
    },
    [filters, onFiltersChange]
  );

  const handleStatusChange = useCallback(
    (values: string[]) => {
      onFiltersChange({ ...filters, statuses: values });
    },
    [filters, onFiltersChange]
  );

  const handlePriorityChange = useCallback(
    (values: string[]) => {
      onFiltersChange({ ...filters, priorities: values });
    },
    [filters, onFiltersChange]
  );

  const handleStageChange = useCallback(
    (values: string[]) => {
      onFiltersChange({ ...filters, stages: values });
    },
    [filters, onFiltersChange]
  );

  const handleCategoryChange = useCallback(
    (value: string | undefined) => {
      onFiltersChange({ ...filters, category: value });
    },
    [filters, onFiltersChange]
  );

  const handleClearFilters = useCallback(() => {
    onFiltersChange({});
  }, [onFiltersChange]);

  return (
    <div
      style={{
        padding: '12px 16px',
        background: '#FFFFFF',
        borderBottom: '1px solid #F0F0F0',
        display: 'flex',
        flexDirection: 'column',
        gap: 8,
      }}
    >
      {/* 主工具栏 */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, flexWrap: 'wrap' }}>
        {/* 系统标题 */}
        <div style={{ fontWeight: 700, fontSize: 16, color: '#001529', flexShrink: 0 }}>
          XPBET 功能地图
        </div>

        {/* 搜索框 */}
        <Input
          prefix={<SearchOutlined style={{ color: '#BFBFBF' }} />}
          placeholder="搜索模块或功能..."
          value={filters.keyword ?? ''}
          onChange={handleKeywordChange}
          allowClear
          style={{ width: 220 }}
        />

        {/* 分类快速过滤 */}
        <Select
          placeholder="选择分类"
          value={filters.category}
          onChange={handleCategoryChange}
          allowClear
          style={{ width: 180 }}
        >
          {CATEGORY_OPTIONS.map((cat) => (
            <Option key={cat} value={cat}>
              {cat}
            </Option>
          ))}
        </Select>

        {/* 高级过滤器切换 */}
        <Tooltip title="高级过滤">
          <Badge count={activeFilterCount} size="small">
            <Button
              icon={<FilterOutlined />}
              onClick={() => setShowAdvancedFilters((v) => !v)}
              type={showAdvancedFilters ? 'primary' : 'default'}
            >
              过滤器
            </Button>
          </Badge>
        </Tooltip>

        {/* 视图切换 */}
        <Space.Compact>
          <Tooltip title="水平布局">
            <Button
              icon={<MenuOutlined />}
              type={direction === 'H' ? 'primary' : 'default'}
              onClick={() => onDirectionChange('H')}
            />
          </Tooltip>
          <Tooltip title="垂直布局">
            <Button
              icon={<AppstoreOutlined />}
              type={direction === 'V' ? 'primary' : 'default'}
              onClick={() => onDirectionChange('V')}
            />
          </Tooltip>
        </Space.Compact>

        {/* 刷新按钮 */}
        <Tooltip title="从飞书刷新数据">
          <Button
            icon={<ReloadOutlined spin={loading} />}
            onClick={onRefresh}
            loading={loading}
          >
            刷新
          </Button>
        </Tooltip>

        {/* 节点计数 */}
        {totalCount !== undefined && (
          <span style={{ fontSize: 12, color: '#8C8C8C', marginLeft: 'auto' }}>
            {filteredCount !== undefined && filteredCount !== totalCount
              ? `已筛选 ${filteredCount} / ${totalCount} 个节点`
              : `共 ${totalCount} 个节点`}
          </span>
        )}
      </div>

      {/* 高级过滤器展开区域 */}
      {showAdvancedFilters && (
        <div
          style={{
            display: 'flex',
            gap: 12,
            flexWrap: 'wrap',
            padding: '8px 0',
            borderTop: '1px solid #F5F5F5',
          }}
        >
          {/* 状态过滤 */}
          <Select
            mode="multiple"
            placeholder="按状态过滤"
            value={filters.statuses ?? []}
            onChange={handleStatusChange}
            style={{ minWidth: 200 }}
            maxTagCount={2}
          >
            {STATUS_OPTIONS.map((s) => (
              <Option key={s} value={s}>
                {s}
              </Option>
            ))}
          </Select>

          {/* 优先级过滤 */}
          <Select
            mode="multiple"
            placeholder="按优先级过滤"
            value={filters.priorities ?? []}
            onChange={handlePriorityChange}
            style={{ minWidth: 180 }}
          >
            {PRIORITY_OPTIONS.map((p) => (
              <Option key={p} value={p}>
                {p}
              </Option>
            ))}
          </Select>

          {/* 阶段过滤 */}
          <Select
            mode="multiple"
            placeholder="按阶段过滤"
            value={filters.stages ?? []}
            onChange={handleStageChange}
            style={{ minWidth: 200 }}
            maxTagCount={2}
          >
            {STAGE_OPTIONS.map((s) => (
              <Option key={s} value={s}>
                {s}
              </Option>
            ))}
          </Select>

          {/* 清除过滤器 */}
          {activeFilterCount > 0 && (
            <Button size="small" onClick={handleClearFilters}>
              清除全部过滤
            </Button>
          )}
        </div>
      )}
    </div>
  );
};
