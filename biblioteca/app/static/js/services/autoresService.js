/**
 * SERVICIO DE AUTORES
 * Conecta con los endpoints reales de /api/v1/autores
 */

import { api } from './api.js';

export const autoresService = {
  async listar(filtros = {}) {
    return api.get('/autores', filtros);
  },

  async obtener(id) {
    return api.get(`/autores/${id}`);
  },

  async crear(datos) {
    // datos: { nombre, nacionalidad?, anio_nacimiento? }
    return api.post('/autores', datos);
  },

  async actualizar(id, datos) {
    return api.patch(`/autores/${id}`, datos);
  },

  async eliminar(id) {
    return api.delete(`/autores/${id}`);
  }
};
