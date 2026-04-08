/**
 * G6 自定义节点注册
 * XPBET 全球站功能地图管理系统
 *
 * 注册 'xpbet-node' 自定义节点类型，根据节点类型（root/category/module/feature）
 * 渲染不同样式的矩形节点，支持状态背景色和优先级边框色。
 */

import G6, { type IGroup, type Item, type ModelConfig } from '@antv/g6';

// ==================== 节点尺寸配置 ====================

const NODE_SIZE_CONFIG = {
  root: { width: 160, height: 48, radius: 8, fontSize: 16, fontWeight: 'bold' },
  category: { width: 140, height: 40, radius: 6, fontSize: 14, fontWeight: '600' },
  module: { width: 'auto', height: 36, radius: 4, fontSize: 13, fontWeight: 'normal' },
  feature: { width: 'auto', height: 28, radius: 4, fontSize: 12, fontWeight: 'normal' },
} as const;

// ==================== 自定义节点注册 ====================

/**
 * 注册 XPBET 自定义节点
 * 必须在 G6 图实例化之前调用
 */
export function registerXPBETNode(): void {
  G6.registerNode(
    'xpbet-node',
    {
      /**
       * 绘制节点主体
       */
      draw(cfg: ModelConfig | undefined, group: IGroup | undefined) {
        if (!cfg || !group) return group?.addShape('rect', {}) as any;

        const nodeType = (cfg.type as string) || 'feature';
        const label = String(cfg.label ?? '');
        const style = (cfg.style as Record<string, unknown>) ?? {};
        const sizeConfig = NODE_SIZE_CONFIG[nodeType as keyof typeof NODE_SIZE_CONFIG] ?? NODE_SIZE_CONFIG.feature;

        // 计算节点宽度（auto 时根据文字长度动态计算）
        const nodeWidth =
          sizeConfig.width === 'auto'
            ? Math.max(label.length * (sizeConfig.fontSize * 0.65) + 32, 80)
            : sizeConfig.width;
        const nodeHeight = sizeConfig.height;

        // ── 绘制节点背景矩形 ──────────────────────────────────────────
        const rect = group.addShape('rect', {
          attrs: {
            x: -nodeWidth / 2,
            y: -nodeHeight / 2,
            width: nodeWidth,
            height: nodeHeight,
            radius: sizeConfig.radius,
            fill: (style.fill as string) ?? '#FFFFFF',
            stroke: (style.stroke as string) ?? '#D9D9D9',
            lineWidth: (style.lineWidth as number) ?? 2,
            cursor: 'pointer',
            // 悬浮时添加阴影效果
            shadowColor: 'rgba(0, 0, 0, 0.1)',
            shadowBlur: 0,
          },
          name: 'node-rect',
          draggable: true,
        });

        // ── 绘制节点文本 ──────────────────────────────────────────────
        // 文字颜色：深色背景（开发中蓝色/完成绿色）使用白色文字，浅色背景使用深色文字
        const fillColor = (style.fill as string) ?? '#FFFFFF';
        const isDarkBackground = isDarkColor(fillColor);
        const textColor = isDarkBackground ? '#FFFFFF' : '#333333';

        group.addShape('text', {
          attrs: {
            x: 0,
            y: 0,
            text: truncateLabel(label, nodeType),
            fontSize: sizeConfig.fontSize,
            fontWeight: sizeConfig.fontWeight,
            fill: textColor,
            textAlign: 'center',
            textBaseline: 'middle',
            cursor: 'pointer',
          },
          name: 'node-label',
          draggable: true,
        });

        // ── 功能节点：绘制文档链接图标 ───────────────────────────────
        if (nodeType === 'feature') {
          const data = cfg.data as Record<string, unknown> | undefined;
          if (data?.docLink) {
            group.addShape('text', {
              attrs: {
                x: nodeWidth / 2 - 12,
                y: -nodeHeight / 2 + 8,
                text: '↗',
                fontSize: 10,
                fill: isDarkBackground ? 'rgba(255,255,255,0.8)' : '#1890FF',
                textAlign: 'center',
                textBaseline: 'top',
                cursor: 'pointer',
              },
              name: 'doc-link-icon',
            });
          }
        }

        return rect;
      },

      /**
       * 节点状态变化时的样式更新
       */
      setState(name: string | undefined, value: boolean | string | undefined, item: Item | undefined) {
        if (!name || !item) return;
        const group = item.getContainer();
        const rect = group.find((e) => e.get('name') === 'node-rect');
        if (!rect) return;

        if (name === 'hover') {
          if (value) {
            rect.attr('shadowBlur', 8);
            rect.attr('shadowColor', 'rgba(0, 0, 0, 0.2)');
          } else {
            rect.attr('shadowBlur', 0);
          }
        }

        if (name === 'selected') {
          if (value) {
            rect.attr('lineWidth', 3);
          } else {
            const model = item.getModel();
            const style = (model.style as Record<string, unknown>) ?? {};
            rect.attr('lineWidth', (style.lineWidth as number) ?? 2);
          }
        }

        if (name === 'dimmed') {
          // 过滤时不匹配的节点降低透明度
          const opacity = value ? 0.2 : 1;
          group.get('children').forEach((child: any) => {
            child.attr('opacity', opacity);
          });
        }
      },

      /**
       * 获取节点锚点（连线起止点）
       */
      getAnchorPoints() {
        return [
          [0, 0.5], // 左中
          [1, 0.5], // 右中
        ];
      },
    },
    'single-node'
  );
}

// ==================== 工具函数 ====================

/**
 * 判断颜色是否为深色（用于决定文字颜色）
 * 基于 YIQ 亮度公式
 */
function isDarkColor(hexColor: string): boolean {
  const hex = hexColor.replace('#', '');
  if (hex.length !== 6) return false;
  const r = parseInt(hex.slice(0, 2), 16);
  const g = parseInt(hex.slice(2, 4), 16);
  const b = parseInt(hex.slice(4, 6), 16);
  const yiq = (r * 299 + g * 587 + b * 114) / 1000;
  return yiq < 128;
}

/**
 * 截断过长的节点标签
 */
function truncateLabel(label: string, nodeType: string): string {
  const maxLength = nodeType === 'root' ? 20 : nodeType === 'category' ? 16 : 14;
  if (label.length <= maxLength) return label;
  return label.slice(0, maxLength - 1) + '…';
}
