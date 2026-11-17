/**
 * SERVICIO DE CATEGORÍAS
 * Conecta con los endpoints reales de /api/v1/categorias
 */

import { api } from './api.js';

export const categoriasService = {
  async listar(filtros = {}) {
    return api.get('/categorias', filtros);
  },

  async obtener(id) {
    return api.get(`/categorias/${id}`);
  },

  async crear(datos) {
    // datos: { nombre, descripcion? }
    return api.post('/categorias', datos);
  },

  async actualizar(id, datos) {
    return api.patch(`/categorias/${id}`, datos);
  },

  async eliminar(id) {
    return api.delete(`/categorias/${id}`);
  }
};
