/**
 * request.js (ES Module Version)
 * 原生 JavaScript HTTP 请求封装库
 * 无依赖，适用于现代浏览器环境
 */

// ================= 配置区域 =================
const CONFIG = {
  // 基础路径：适配 Nginx 多站点部署
  // 留空表示使用相对路径 (推荐)，或者填写 '/api'
  baseURL: '', 
  
  // 默认超时时间 (毫秒)
  timeout: 15000,
  
  // 默认请求头
  defaultHeaders: {
    'Content-Type': 'application/json'
  },

  // 是否自动携带 Cookie (跨域场景需开启)
  credentials: 'same-origin' // 可选: 'include', 'omit', 'same-origin'
};

// ================= 工具函数 =================

/**
 * 将对象转换为查询字符串
 * @param {Object} params 
 * @returns {string}
 */
function buildQueryString(params) {
  if (!params || typeof params !== 'object') return '';
  const searchParams = new URLSearchParams();
  for (const key in params) {
    if (Object.hasOwnProperty.call(params, key) && params[key] !== undefined && params[key] !== null) {
      searchParams.append(key, params[key]);
    }
  }
  return searchParams.toString();
}

/**
 * 处理 URL 拼接
 * @param {string} url 
 * @returns {string}
 */
function resolveUrl(url) {
  // 如果 url 已经是 http/https 开头，直接使用（忽略 baseURL）
  if (/^https?:\/\//i.test(url)) {
    return url;
  }
  // 否则拼接 baseURL
  const base = CONFIG.baseURL.endsWith('/') ? CONFIG.baseURL.slice(0, -1) : CONFIG.baseURL;
  const path = url.startsWith('/') ? url : '/' + url;
  return base + path;
}

// ================= 核心请求函数 =================

/**
 * 通用请求方法
 * @param {string} url - 请求地址
 * @param {string} method - 请求方法 (GET, POST, PUT, DELETE, PATCH)
 * @param {any} data - 请求数据 (对象、FormData 或 null)
 * @param {Object} options - 额外配置 (headers, timeout, credentials 等)
 * @returns {Promise<any>}
 */
export async function request(url, method = 'GET', data = null, options = {}) {
  const finalUrl = resolveUrl(url);
  
  // 合并配置
  const config = {
    method: method.toUpperCase(),
    headers: { ...CONFIG.defaultHeaders, ...(options.headers || {}) },
    credentials: options.credentials || CONFIG.credentials,
    signal: null // 用于超时控制
  };

  // 1. 处理数据 (Body 和 Query Params)
  const isFormData = data instanceof FormData;
  const isGetOrDelete = config.method === 'GET' || config.method === 'DELETE';

  if (isGetOrDelete) {
    // GET/DELETE: 数据作为查询参数拼接到 URL
    if (data && typeof data === 'object' && !isFormData) {
      const qs = buildQueryString(data);
      if (qs) {
        const separator = finalUrl.includes('?') ? '&' : '?';
        // 注意：这里我们直接修改最终使用的 URL，而不是 config.url (fetch 第一个参数)
        const targetUrl = `${finalUrl}${separator}${qs}`;
        // fetch 直接使用 targetUrl
        config.url = targetUrl; 
      } else {
        config.url = finalUrl;
      }
    } else {
      config.url = finalUrl;
    }
    config.body = undefined;
    
    if (isFormData) {
      delete config.headers['Content-Type'];
    }

  } else {
    // POST/PUT/PATCH: 数据放在 Body 中
    config.url = finalUrl;

    if (isFormData) {
      delete config.headers['Content-Type'];
      config.body = data;
    } else if (data !== null && typeof data === 'object') {
      config.body = JSON.stringify(data);
    } else if (typeof data === 'string') {
      config.body = data;
    }
  }

  // 2. 设置超时控制
  const controller = new AbortController();
  const timeoutMs = options.timeout || CONFIG.timeout;
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);
  config.signal = controller.signal;

  const clearTimer = () => clearTimeout(timeoutId);

  try {
    console.log(`[Request] ${config.method} ${config.url}`, config.body || '');

    // 注意：fetch 的第一个参数必须是完整的 URL 字符串
    const response = await fetch(config.url, config);
    clearTimer();

    if (!response.ok) {
      let errorMsg = `HTTP Error: ${response.status} ${response.statusText}`;
      try {
        const errData = await response.clone().json();
        errorMsg = errData.message || errData.error || errorMsg;
      } catch (e) {
        // 非 JSON 响应
      }
      const error = new Error(errorMsg);
      error.status = response.status;
      error.response = response;
      throw error;
    }

    const contentType = response.headers.get('content-type');
    if (contentType && contentType.includes('application/json')) {
      const json = await response.json();
      console.log(`[Response] ${config.url}`, json);
      return json;
    } else {
      const text = await response.text();
      console.log(`[Response] ${config.url}`, text);
      return text;
    }

  } catch (error) {
    clearTimer();
    if (error.name === 'AbortError') {
      const timeoutError = new Error(`请求超时 (${timeoutMs}ms)`);
      timeoutError.code = 'TIMEOUT';
      console.error('[Request Timeout]', config.url);
      throw timeoutError;
    }
    console.error('[Request Failed]', error);
    throw error;
  }
}

// ================= 配置管理函数 =================

/**
 * 更新全局配置
 * @param {Object} newConfig 
 */
export function configure(newConfig) {
  Object.assign(CONFIG, newConfig);
  console.log('[Request] Config updated:', CONFIG);
}

// ================= 便捷方法封装 =================

export const http = {
  /**
   * 更新配置 (别名)
   */
  config: configure,

  /**
   * GET 请求
   */
  get: (url, params, options) => request(url, 'GET', params, options),

  /**
   * POST 请求
   */
  post: (url, data, options) => request(url, 'POST', data, options),

  /**
   * PUT 请求
   */
  put: (url, data, options) => request(url, 'PUT', data, options),

  /**
   * DELETE 请求
   */
  del: (url, params, options) => request(url, 'DELETE', params, options),

  /**
   * PATCH 请求
   */
  patch: (url, data, options) => request(url, 'PATCH', data, options),

  /**
   * 文件上传
   */
  upload: (url, fileInputElem, extraData = {}, options = {}) => {
    const formData = new FormData();
    const files = fileInputElem.files;
    
    if (!files || files.length === 0) {
      return Promise.reject(new Error('未选择文件'));
    }

    formData.append('file', files[0]);

    for (const key in extraData) {
      if (Object.hasOwnProperty.call(extraData, key)) {
        formData.append(key, extraData[key]);
      }
    }

    if (options.headers) {
      delete options.headers['Content-Type'];
    }

    return request(url, 'POST', formData, options);
  }
};

// 默认导出 http 对象，方便 import http from ...
export default http;