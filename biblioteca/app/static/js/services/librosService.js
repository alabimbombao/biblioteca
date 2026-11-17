/**
 * SERVICIO DE LIBROS
 * Conecta con los endpoints reales de /api/v1/libros
 */

import { api } from './api.js';

export const librosService = {
  async listar(filtros = {}) {
    return api.get('/libros', filtros);
  },

  async obtener(id) {
    return api.get(`/libros/${id}`);
  },

  async crear(datos) {
    // datos: { titulo, isbn, anio_publicacion, ejemplares, autor_id, categoria_ids }
    return api.post('/libros', datos);
  },

  async actualizar(id, cambios) {
    // cambios: { titulo?, anio_publicacion?, ejemplares?, categoria_ids? }
    return api.patch(`/libros/${id}`, cambios);
  },

  async eliminar(id) {
    return api.delete(`/libros/${id}`);
  },

  async librosDeAutor(autorId, skip = 0, limit = 20) {
    return api.get(`/autores/${autorId}/libros`, { skip, limit });
  },

  async subirPortada(libroId, archivoFile) {
    const formData = new FormData();
    formData.append('archivo', archivoFile);
    return api.post(`/libros/${libroId}/portada`, formData, true);
  },

  async eliminarPortada(libroId) {
    return api.delete(`/libros/${libroId}/portada`);
  }
};
