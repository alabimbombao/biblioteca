/**
 * SERVICIO DE PRÉSTAMOS
 * Conecta con los endpoints reales de /api/v1/prestamos
 */

import { api } from './api.js';

export const prestamosService = {
  async listar(filtros = {}) {
    return api.get('/prestamos', filtros);
  },

  async obtener(id) {
    return api.get(`/prestamos/${id}`);
  },

  async crear(datos) {
    // datos: { socio_id, libro_id, fecha_prestamo?, dias? }
    return api.post('/prestamos', datos);
  },

  async registrarDevolucion(id, fechaDevolucion = null) {
    const payload = fechaDevolucion ? { fecha_devolucion: fechaDevolucion } : {};
    return api.post(`/prestamos/${id}/devolucion`, payload);
  },

  async pagarMulta(id) {
    return api.post(`/prestamos/${id}/pago-multa`);
  }
};
