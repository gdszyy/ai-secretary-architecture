/**
 * ErrorPanel - 错误状态展示组件
 * XPBET 全球站功能地图管理系统
 *
 * 在飞书 Bitable API 请求失败时显示，提供错误信息和重试按钮。
 */

import React from 'react';

interface ErrorPanelProps {
  /** 错误信息 */
  message: string;
  /** 重试回调 */
  onRetry?: () => void;
  /** 是否为警告（有 fallback 数据时使用） */
  isWarning?: boolean;
}

export const ErrorPanel: React.FC<ErrorPanelProps> = ({
  message,
  onRetry,
  isWarning = false,
}) => {
  const iconColor = isWarning ? '#FA8C16' : '#FF4D4F';
  const bgColor = isWarning ? '#FFFBE6' : '#FFF2F0';
  const borderColor = isWarning ? '#FFD591' : '#FFCCC7';

  return (
    <div
      style={{
        width: '100%',
        padding: '12px 16px',
        background: bgColor,
        border: `1px solid ${borderColor}`,
        borderRadius: 8,
        display: 'flex',
        alignItems: 'flex-start',
        gap: 12,
        fontFamily: "'PingFang SC', 'Microsoft YaHei', -apple-system, BlinkMacSystemFont, sans-serif",
      }}
    >
      {/* 图标 */}
      <svg
        width="18"
        height="18"
        viewBox="0 0 18 18"
        fill="none"
        style={{ flexShrink: 0, marginTop: 1 }}
      >
        {isWarning ? (
          <path
            d="M9 1L17 16H1L9 1Z"
            stroke={iconColor}
            strokeWidth="1.5"
            strokeLinejoin="round"
          />
        ) : (
          <circle cx="9" cy="9" r="8" stroke={iconColor} strokeWidth="1.5" />
        )}
        <path
          d={isWarning ? 'M9 7V10' : 'M9 6V10'}
          stroke={iconColor}
          strokeWidth="1.5"
          strokeLinecap="round"
        />
        <circle cx="9" cy="13" r="0.75" fill={iconColor} />
      </svg>

      {/* 内容区 */}
      <div style={{ flex: 1 }}>
        <div
          style={{
            fontSize: 13,
            fontWeight: 500,
            color: isWarning ? '#AD6800' : '#CF1322',
            marginBottom: 4,
          }}
        >
          {isWarning ? '数据加载警告' : '数据加载失败'}
        </div>
        <div
          style={{
            fontSize: 12,
            color: isWarning ? '#874D00' : '#820014',
            lineHeight: '1.6',
            wordBreak: 'break-all',
          }}
        >
          {message}
        </div>
      </div>

      {/* 重试按钮 */}
      {onRetry && (
        <button
          onClick={onRetry}
          style={{
            flexShrink: 0,
            padding: '4px 12px',
            fontSize: 12,
            color: iconColor,
            background: 'transparent',
            border: `1px solid ${iconColor}`,
            borderRadius: 4,
            cursor: 'pointer',
            transition: 'all 0.15s',
            whiteSpace: 'nowrap',
          }}
          onMouseEnter={(e) => {
            (e.currentTarget as HTMLButtonElement).style.background = isWarning
              ? '#FFF7E6'
              : '#FFF1F0';
          }}
          onMouseLeave={(e) => {
            (e.currentTarget as HTMLButtonElement).style.background = 'transparent';
          }}
        >
          重新加载
        </button>
      )}
    </div>
  );
};

/**
 * FullPageError - 全屏错误展示（API 完全失败且无 fallback 时使用）
 */
export const FullPageError: React.FC<ErrorPanelProps> = ({ message, onRetry }) => {
  return (
    <div
      style={{
        width: '100vw',
        height: '100vh',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        background: '#F7F8FA',
        gap: 20,
        fontFamily: "'PingFang SC', 'Microsoft YaHei', -apple-system, BlinkMacSystemFont, sans-serif",
      }}
    >
      {/* 错误图标 */}
      <svg width="64" height="64" viewBox="0 0 64 64" fill="none">
        <circle cx="32" cy="32" r="30" stroke="#FF4D4F" strokeWidth="2" />
        <path
          d="M32 20V36"
          stroke="#FF4D4F"
          strokeWidth="3"
          strokeLinecap="round"
        />
        <circle cx="32" cy="44" r="2" fill="#FF4D4F" />
      </svg>

      {/* 错误标题 */}
      <div style={{ fontSize: 18, fontWeight: 600, color: '#1A1A2E' }}>
        数据加载失败
      </div>

      {/* 错误信息 */}
      <div
        style={{
          fontSize: 13,
          color: '#8C8C8C',
          maxWidth: 400,
          textAlign: 'center',
          lineHeight: '1.7',
          padding: '0 24px',
        }}
      >
        {message}
      </div>

      {/* 重试按钮 */}
      {onRetry && (
        <button
          onClick={onRetry}
          style={{
            padding: '8px 24px',
            fontSize: 14,
            color: '#FFFFFF',
            background: '#1677FF',
            border: 'none',
            borderRadius: 6,
            cursor: 'pointer',
            transition: 'background 0.15s',
          }}
          onMouseEnter={(e) => {
            (e.currentTarget as HTMLButtonElement).style.background = '#4096FF';
          }}
          onMouseLeave={(e) => {
            (e.currentTarget as HTMLButtonElement).style.background = '#1677FF';
          }}
        >
          重新加载
        </button>
      )}

      {/* 配置提示 */}
      <div
        style={{
          fontSize: 11,
          color: '#BFBFBF',
          textAlign: 'center',
          lineHeight: '1.8',
        }}
      >
        提示：可在 .env 文件中设置 VITE_USE_STATIC_DATA=true 切换为离线模式
      </div>
    </div>
  );
};

export default ErrorPanel;
