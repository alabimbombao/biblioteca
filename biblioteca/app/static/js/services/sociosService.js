/**
 * SERVICIO DE SOCIOS
 * Conecta con los endpoints reales de /api/v1/socios
 */

import { api } from './api.js';

export const sociosService = {
  async listar(filtros = {}) {
    return api.get('/socios', filtros);
  },

  async obtener(id) {
    return api.get(`/socios/${id}`);
  },

  async crear(datos) {
    // datos: { nombre, email, telefono? }
    return api.post('/socios', datos);
  },

  async actualizar(id, datos) {
    return api.patch(`/socios/${id}`, datos);
  },

  async eliminar(id) {
    return api.delete(`/socios/${id}`);
  },

  async prestamosDeSocio(socioId, skip = 0, limit = 20, estado = null) {
    return api.get(`/socios/${socioId}/prestamos`, { skip, limit, estado });
  },

  // Endpoints del propio socio autenticado
  async miPerfil() {
    return api.get('/socios/me');
  },

  async actualizarMiPerfil(datos) {
    return api.patch('/socios/me', datos);
  },

  async misPrestamos(skip = 0, limit = 20, estado = null) {
    return api.get('/socios/me/prestamos', { skip, limit, estado });
  },

  async misMultas() {
    return api.get('/socios/me/multas');
  }
};
