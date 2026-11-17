/**
 * CLIENTE HTTP CENTRALIZADO (API CLIENT)
 * Gestiona peticiones, inyección de tokens JWT, refresco automático y manejo de errores.
 */

import { CONFIG } from '../config.js';

class ApiClient {
  constructor() {
    this.baseUrl = CONFIG.API_BASE_URL;
    this.isRefreshing = false;
    this.failedQueue = [];
  }

  getAccessToken() {
    return localStorage.getItem(CONFIG.STORAGE_KEYS.ACCESS_TOKEN);
  }

  getRefreshToken() {
    return localStorage.getItem(CONFIG.STORAGE_KEYS.REFRESH_TOKEN);
  }

  setTokens(accessToken, refreshToken) {
    if (accessToken) localStorage.setItem(CONFIG.STORAGE_KEYS.ACCESS_TOKEN, accessToken);
    if (refreshToken) localStorage.setItem(CONFIG.STORAGE_KEYS.REFRESH_TOKEN, refreshToken);
  }

  clearTokens() {
    localStorage.removeItem(CONFIG.STORAGE_KEYS.ACCESS_TOKEN);
    localStorage.removeItem(CONFIG.STORAGE_KEYS.REFRESH_TOKEN);
    localStorage.removeItem(CONFIG.STORAGE_KEYS.USER);
  }

  async request(endpoint, options = {}) {
    const url = endpoint.startsWith('http') ? endpoint : `${this.baseUrl}${endpoint}`;
    const headers = options.headers ? { ...options.headers } : {};

    // Adjuntar Bearer Token si existe
    const token = this.getAccessToken();
    if (token && !headers['Authorization']) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    // Configurar Content-Type si no es FormData
    if (!(options.body instanceof FormData) && !headers['Content-Type']) {
      headers['Content-Type'] = 'application/json';
    }

    options.headers = headers;

    try {
      const response = await fetch(url, options);

      // Si recibimos 204 No Content
      if (response.status === 204) {
        return null;
      }

      // Manejar token expirado (401) e intentar refresco
      if (response.status === 401 && this.getRefreshToken() && !options._retry) {
        options._retry = true;
        const refreshed = await this.refreshToken();
        if (refreshed) {
          options.headers['Authorization'] = `Bearer ${this.getAccessToken()}`;
          return fetch(url, options).then(res => res.status === 204 ? null : res.json());
        }
      }

      // Extraer cuerpo JSON si existe
      let data = null;
      const contentType = response.headers.get('content-type');
      if (contentType && contentType.includes('application/json')) {
        data = await response.json();
      } else {
        const text = await response.text();
        try { data = JSON.parse(text); } catch { data = text; }
      }

      // Si la respuesta no es 2xx, lanzar error procesado
      if (!response.ok) {
        const errorMessage = this.formatErrorDetail(data, response.status);
        const error = new Error(errorMessage);
        error.status = response.status;
        error.data = data;
        throw error;
      }

      return data;
    } catch (err) {
      throw err;
    }
  }

  async refreshToken() {
    const refreshToken = this.getRefreshToken();
    if (!refreshToken) return false;

    try {
      const res = await fetch(`${this.baseUrl}/auth/refresh`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh_token: refreshToken })
      });

      if (!res.ok) {
        this.clearTokens();
        return false;
      }

      const data = await res.json();
      this.setTokens(data.access_token, data.refresh_token);
      return true;
    } catch {
      this.clearTokens();
      return false;
    }
  }

  formatErrorDetail(data, status) {
    if (!data) return `Error en la petición (Código ${status})`;
    if (typeof data === 'string') return data;
    if (data.detail) {
      if (typeof data.detail === 'string') return data.detail;
      if (Array.isArray(data.detail)) {
        // Errores de validación Pydantic
        return data.detail.map(err => {
          const campo = err.loc ? err.loc.join('.') : 'campo';
          return `${campo}: ${err.msg}`;
        }).join(' · ');
      }
      return JSON.stringify(data.detail);
    }
    return JSON.stringify(data);
  }

  // Métodos auxiliares
  get(endpoint, params = null) {
    let url = endpoint;
    if (params) {
      const filteredParams = Object.fromEntries(
        Object.entries(params).filter(([_, v]) => v !== null && v !== undefined && v !== '')
      );
      const query = new URLSearchParams(filteredParams).toString();
      if (query) url += (url.includes('?') ? '&' : '?') + query;
    }
    return this.request(url, { method: 'GET' });
  }

  post(endpoint, body = null, isFormData = false) {
    return this.request(endpoint, {
      method: 'POST',
      body: isFormData ? body : (body ? JSON.stringify(body) : null)
    });
  }

  patch(endpoint, body = null) {
    return this.request(endpoint, {
      method: 'PATCH',
      body: body ? JSON.stringify(body) : null
    });
  }

  delete(endpoint) {
    return this.request(endpoint, { method: 'DELETE' });
  }
}

export const api = new ApiClient();
