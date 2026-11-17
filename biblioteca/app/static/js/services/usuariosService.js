/**
 * SERVICIO DE USUARIOS (SOLO ADMINISTRADOR)
 * Conecta con los endpoints reales de /api/v1/usuarios
 */

import { api } from './api.js';

export const usuariosService = {
  async listar(filtros = {}) {
    return api.get('/usuarios', filtros);
  },

  async crear(datos) {
    // datos: { email, password, rol } (admin o bibliotecario)
    return api.post('/usuarios', datos);
  },

  async cambiarRol(id, rol) {
    return api.patch(`/usuarios/${id}/rol`, { rol });
  },

  async cambiarActivo(id, activo) {
    return api.patch(`/usuarios/${id}/activo`, { activo });
  }
};
