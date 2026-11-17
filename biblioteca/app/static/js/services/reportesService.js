/**
 * SERVICIO DE REPORTES (SOLO STAFF)
 * Conecta con los endpoints reales de /api/v1/reportes
 */

import { api } from './api.js';

export const reportesService = {
  async resumen() {
    return api.get('/reportes/resumen');
  },

  async librosMasPrestados(limite = 5) {
    return api.get('/reportes/libros-mas-prestados', { limite });
  },

  async categoriasTotalLibros() {
    return api.get('/reportes/categorias');
  },

  async prestamosVencidos() {
    return api.get('/reportes/prestamos-vencidos');
  },

  async sociosConMultas() {
    return api.get('/reportes/socios-con-multas');
  },

  async autores() {
    return api.get('/reportes/autores');
  }
};
