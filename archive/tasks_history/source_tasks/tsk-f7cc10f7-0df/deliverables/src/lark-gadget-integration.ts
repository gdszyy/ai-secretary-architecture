/**
 * 飞书小组件 (Lark Gadget) 集成示例
 * XPBET 全球站功能地图管理系统
 *
 * 本文件展示如何在飞书 Gadget 环境中实现免登授权和文档跳转。
 * 飞书 JSSDK 文档: https://open.feishu.cn/document/client-docs/gadget/introduction
 *
 * 使用前置条件:
 * 1. 在 HTML 中引入飞书 JSSDK: <script src="https://lf1-cdn-tos.bytegoofy.com/goofy/lark/op/h5-js-sdk-1.5.16/index.js"></script>
 * 2. 或通过 npm 安装: npm install @feishu/jssdk
 */

// ==================== 类型声明 ====================

/** 飞书 JSSDK 全局对象类型声明（简化版） */
declare const tt: {
  /** 获取当前用户的授权码 */
  requestAuthCode: (options: {
    appId: string;
  }) => Promise<{ code: string }>;

  /** 在飞书内打开文档 */
  openDocument: (options: {
    url: string;
    /** 文档类型: docx/wiki/bitable */
    type?: 'docx' | 'wiki' | 'bitable';
  }) => void;

  /** 获取当前运行环境信息 */
  getSystemInfo: () => Promise<{
    platform: 'ios' | 'android' | 'pc' | 'web';
    appVersion: string;
  }>;

  /** 设置导航栏标题 */
  setNavigationBarTitle: (options: { title: string }) => void;
};

// ==================== 环境检测 ====================

/**
 * 检测当前是否在飞书 Gadget 环境中运行
 */
export function isLarkGadgetEnvironment(): boolean {
  return (
    typeof window !== 'undefined' &&
    (navigator.userAgent.toLowerCase().includes('lark') ||
      navigator.userAgent.toLowerCase().includes('feishu')) &&
    typeof tt !== 'undefined'
  );
}

// ==================== 免登授权 ====================

/**
 * 飞书 Gadget 免登授权
 * 获取当前飞书用户的授权码，用于后续 API 调用
 *
 * @param appId 飞书应用 App ID
 * @returns 授权码（一次性使用，有效期 5 分钟）
 */
export async function requestLarkAuthCode(appId: string): Promise<string> {
  if (!isLarkGadgetEnvironment()) {
    throw new Error('当前不在飞书 Gadget 环境中，无法获取授权码');
  }

  try {
    const { code } = await tt.requestAuthCode({ appId });
    console.log('[LarkGadget] 授权码获取成功');
    return code;
  } catch (error) {
    console.error('[LarkGadget] 授权码获取失败:', error);
    throw new Error('飞书授权失败，请重试');
  }
}

/**
 * 通过授权码换取用户信息
 * 注意：此操作需要后端服务配合，不能在前端直接完成（防止 App Secret 泄露）
 *
 * @param authCode 飞书授权码
 * @returns 用户信息（通过后端 API 获取）
 */
export async function getUserInfoByAuthCode(authCode: string): Promise<{
  userId: string;
  name: string;
  email: string;
  avatarUrl: string;
}> {
  // 将授权码发送到后端，后端调用飞书 API 换取用户信息
  const response = await fetch('/api/auth/lark/callback', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ code: authCode }),
  });

  if (!response.ok) {
    throw new Error(`用户信息获取失败: ${response.statusText}`);
  }

  return response.json();
}

// ==================== 文档跳转 ====================

/**
 * 智能打开飞书文档
 * 在飞书 Gadget 环境中使用 JSSDK 在飞书内打开，否则新标签页打开
 *
 * @param url 飞书文档 URL
 */
export function openDocument(url: string): void {
  if (!url) return;

  if (isLarkGadgetEnvironment()) {
    // 在飞书内打开文档（更好的用户体验）
    tt.openDocument({
      url,
      type: detectDocumentType(url),
    });
  } else {
    // 普通浏览器：新标签页打开
    window.open(url, '_blank', 'noopener,noreferrer');
  }
}

/**
 * 根据 URL 检测飞书文档类型
 */
function detectDocumentType(url: string): 'docx' | 'wiki' | 'bitable' {
  if (url.includes('/wiki/')) return 'wiki';
  if (url.includes('/base/') || url.includes('/bitable/')) return 'bitable';
  return 'docx';
}

// ==================== 飞书 Gadget 初始化 ====================

/**
 * 初始化飞书 Gadget 应用
 * 在应用启动时调用，设置导航栏标题等
 */
export async function initLarkGadget(): Promise<void> {
  if (!isLarkGadgetEnvironment()) return;

  try {
    // 设置导航栏标题
    tt.setNavigationBarTitle({ title: 'XPBET 功能地图' });

    // 获取系统信息（可用于适配不同平台）
    const systemInfo = await tt.getSystemInfo();
    console.log('[LarkGadget] 运行平台:', systemInfo.platform);
    console.log('[LarkGadget] 飞书版本:', systemInfo.appVersion);
  } catch (error) {
    console.warn('[LarkGadget] 初始化警告:', error);
  }
}

// ==================== 使用示例 ====================

/**
 * 完整的飞书 Gadget 集成使用示例
 *
 * @example
 * ```typescript
 * import { initLarkGadget, requestLarkAuthCode, openDocument } from './lark-gadget-integration';
 *
 * // 在 App 组件挂载时初始化
 * useEffect(() => {
 *   initLarkGadget();
 * }, []);
 *
 * // 在需要用户身份时获取授权
 * const handleAuth = async () => {
 *   const code = await requestLarkAuthCode(process.env.VITE_LARK_APP_ID);
 *   const userInfo = await getUserInfoByAuthCode(code);
 *   console.log('当前用户:', userInfo.name);
 * };
 *
 * // 在节点双击时打开文档
 * const handleNodeDoubleClick = (node: MindMapNode) => {
 *   if (node.data?.docLink) {
 *     openDocument(node.data.docLink);
 *   }
 * };
 * ```
 */
export const INTEGRATION_EXAMPLE = '详见上方 JSDoc 注释';
