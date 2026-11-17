/**
 * SERVICIO DE AUTENTICACIÓN
 * Conecta con los endpoints reales de /api/v1/auth
 */

import { api } from './api.js';
import { CONFIG } from '../config.js';

export const authService = {
  async login(email, password) {
    const formData = new URLSearchParams();
    formData.append('username', email);
    formData.append('password', password);

    const res = await fetch(`${CONFIG.API_BASE_URL}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: formData
    });

    const data = await res.json();
    if (!res.ok) {
      const msg = data && data.detail ? (typeof data.detail === 'string' ? data.detail : JSON.stringify(data.detail)) : 'Credenciales inválidas';
      throw new Error(msg);
    }

    api.setTokens(data.access_token, data.refresh_token);
    
    // Obtener los datos reales del usuario autenticado
    const profile = await this.getMe();
    localStorage.setItem(CONFIG.STORAGE_KEYS.USER, JSON.stringify(profile));
    return profile;
  },

  async registro(nombre, email, password, telefono = null) {
    return api.post('/auth/registro', { nombre, email, password, telefono });
  },

  async logout() {
    const refreshToken = api.getRefreshToken();
    if (refreshToken) {
      try {
        await api.post('/auth/logout', { refresh_token: refreshToken });
      } catch (e) {
        console.warn('Error revocando sesión en servidor:', e);
      }
    }
    api.clearTokens();
  },

  async getMe() {
    return api.get('/auth/me');
  },

  async cambiarPassword(actual, nueva) {
    return api.patch('/auth/me/password', { actual, nueva });
  },

  getCurrentUser() {
    const raw = localStorage.getItem(CONFIG.STORAGE_KEYS.USER);
    if (!raw) return null;
    try { return JSON.parse(raw); } catch { return null; }
  },

  isAuthenticated() {
    return !!api.getAccessToken();
  }
};
