/**
 * VISTA: PRÉSTAMOS Y CIRCULACIÓN
 * Mesa de control de circulación: registro de préstamos, devoluciones físicas y liquidación de multas.
 */

import { prestamosService } from '../../services/prestamosService.js';
import { librosService } from '../../services/librosService.js';
import { sociosService } from '../../services/sociosService.js';
import { store } from '../../state.js';
import { UI } from '../components.js';

export const prestamosView = {
  skip: 0,
  limit: 15,
  filtroEstado: '',
  prestamos: [],

  async render(container, routeParams = {}) {
    const { currentUser, isStaff } = store.get();

    if (!currentUser) {
      container.innerHTML = UI.emptyState(
        'Acceso de Circulación Protegido',
        'Inicia sesión con tu cuenta autorizada para acceder al libro mayor de préstamos.',
        'Iniciar Sesión',
        'window.appRouter.abrirModalLogin()'
      );
      return;
    }

    container.innerHTML = `
      <div class="space-y-6 animate-fade-in">

        <div class="flex flex-col md:flex-row md:items-center md:justify-between gap-4 pb-4 border-b border-parchment-300">
          <div>
            <span class="text-xs font-display tracking-widest uppercase text-gold font-bold">Mesa de Circulación</span>
            <h2 class="text-2xl sm:text-3xl font-bold font-editorial text-forest">Control de Préstamos</h2>
            <p class="text-xs text-warmgray mt-1">Monitorea los plazos de retorno, devoluciones físicas e infracciones por retraso.</p>
          </div>

          <div class="flex flex-wrap items-center gap-2">
            <select id="filtro-prestamo-estado" onchange="window.prestamosViewInstance.filtrarPorEstado(this.value)" class="px-3 py-2 bg-ivory border border-parchment-300 rounded-xl text-xs text-forest focus:ring-2 focus:ring-forest focus:outline-none">
              <option value="">Todos los Estados</option>
              <option value="activo" ${this.filtroEstado === 'activo' ? 'selected' : ''}>Solo Activos</option>
              <option value="vencido" ${this.filtroEstado === 'vencido' ? 'selected' : ''}>Solo Vencidos</option>
              <option value="devuelto" ${this.filtroEstado === 'devuelto' ? 'selected' : ''}>Solo Devueltos</option>
            </select>

            ${isStaff ? `
              <button onclick="window.prestamosViewInstance.abrirModalRegistrar()" class="inline-flex items-center gap-2 bg-forest hover:bg-forest-light text-parchment-50 font-display uppercase tracking-wider text-xs font-bold px-4 py-2.5 rounded-xl shadow-md transition">
                <i class="fa-solid fa-hand-holding-hand text-gold"></i> Registrar Préstamo
              </button>
            ` : ''}
          </div>
        </div>

        <div class="bg-parchment-light rounded-3xl border border-parchment-300 shadow-sm overflow-hidden">
          <div class="overflow-x-auto">
            <table class="min-w-full divide-y divide-parchment-300 text-xs text-left">
              <thead class="bg-parchment-200 text-forest font-display uppercase tracking-wider text-[11px]">
                <tr>
                  <th class="px-5 py-3.5 font-bold">Registro</th>
                  <th class="px-5 py-3.5 font-bold">Lector / Socio</th>
                  <th class="px-5 py-3.5 font-bold">Obra Prestada</th>
                  <th class="px-5 py-3.5 font-bold">Fecha Préstamo</th>
                  <th class="px-5 py-3.5 font-bold">Fecha Límite</th>
                  <th class="px-5 py-3.5 font-bold">Estado</th>
                  <th class="px-5 py-3.5 font-bold">Multa</th>
                  <th class="px-5 py-3.5 font-bold text-right">Acción</th>
                </tr>
              </thead>
              <tbody id="tabla-prestamos-body" class="divide-y divide-parchment-200 font-sans text-warmgray-dark">
                <tr>
                  <td colspan="8" class="p-8 text-center">${UI.loadingSpinner('Consultando registros de circulación...')}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <div id="prestamos-paginacion-container"></div>

      </div>
    `;

    window.prestamosViewInstance = this;
    await this.cargarPrestamos();

    // Si viene un libro preseleccionado para préstamo inmediato
    if (routeParams.libroId && isStaff) {
      this.abrirModalRegistrar(routeParams.libroId);
    }
  },

  async cargarPrestamos() {
    const tbody = document.getElementById('tabla-prestamos-body');
    const pagContainer = document.getElementById('prestamos-paginacion-container');
    if (!tbody) return;

    try {
      const res = await prestamosService.listar({
        skip: this.skip,
        limit: this.limit,
        estado: this.filtroEstado || null
      });

      const prestamos = res.items || [];
      this.prestamos = prestamos;

      if (prestamos.length === 0) {
        tbody.innerHTML = `<tr><td colspan="8" class="p-8 text-center text-warmgray">No hay préstamos registrados bajo este criterio.</td></tr>`;
        pagContainer.innerHTML = '';
        return;
      }

      const { isStaff } = store.get();

      tbody.innerHTML = prestamos.map(p => {
        const socioNombre = p.socio ? p.socio.nombre : `Socio #${p.socio_id}`;
        const libroTitulo = p.libro ? p.libro.titulo : `Libro #${p.libro_id}`;

        const multaText = p.multa > 0
          ? `<span class="font-bold text-red-700 font-mono text-xs">$${parseFloat(p.multa).toFixed(2)} ${p.multa_pagada ? '<span class="text-emerald-700 text-[10px]">(Pagada)</span>' : '<span class="text-red-600 text-[10px] font-bold">(Pendiente)</span>'}</span>`
          : `<span class="text-warmgray text-xs">$0.00</span>`;

        let btnAccion = '';
        if (isStaff && p.estado !== 'devuelto') {
          btnAccion = `
            <button onclick="window.prestamosViewInstance.registrarDevolucion(${p.id})" class="px-2.5 py-1 bg-forest hover:bg-forest-light text-parchment-50 rounded-lg text-[11px] font-semibold transition shadow-sm">
              <i class="fa-solid fa-arrow-rotate-left text-gold text-[10px]"></i> Devolver
            </button>
          `;
        } else if (isStaff && p.multa > 0 && !p.multa_pagada) {
          btnAccion = `
            <button onclick="window.prestamosViewInstance.pagarMulta(${p.id})" class="px-2.5 py-1 bg-amber-800 hover:bg-amber-900 text-parchment-50 rounded-lg text-[11px] font-semibold transition shadow-sm">
              <i class="fa-solid fa-coins text-gold text-[10px]"></i> Pagar Multa
            </button>
          `;
        }

        return `
          <tr class="hover:bg-parchment-50 transition">
            <td class="px-5 py-3.5 font-mono font-bold text-gold">#${p.id}</td>
            <td class="px-5 py-3.5 font-editorial font-bold text-forest text-sm">${socioNombre}</td>
            <td class="px-5 py-3.5 font-medium text-warmgray-dark">${libroTitulo}</td>
            <td class="px-5 py-3.5 font-mono text-warmgray">${p.fecha_prestamo}</td>
            <td class="px-5 py-3.5 font-mono font-semibold ${p.estado === 'vencido' ? 'text-red-700 font-bold' : 'text-forest'}">${p.fecha_limite}</td>
            <td class="px-5 py-3.5">${UI.loanBadge(p.estado)}</td>
            <td class="px-5 py-3.5">${multaText}</td>
            <td class="px-5 py-3.5 text-right whitespace-nowrap">${btnAccion}</td>
          </tr>
        `;
      }).join('');

      pagContainer.innerHTML = UI.renderPagination(
        res.total,
        this.skip,
        this.limit,
        'window.prestamosViewInstance.cambiarPagina'
      );
    } catch (e) {
      tbody.innerHTML = `<tr><td colspan="8" class="p-8 text-center text-red-800">${e.message}</td></tr>`;
    }
  },

  filtrarPorEstado(estado) {
    this.filtroEstado = estado;
    this.skip = 0;
    this.cargarPrestamos();
  },

  cambiarPagina(nuevoSkip) {
    this.skip = nuevoSkip;
    this.cargarPrestamos();
  },

  async abrirModalRegistrar(preselectedLibroId = null) {
    // Cargar socios y libros disponibles
    let socios = store.get().socios;
    if (socios.length === 0) {
      try {
        const resSocios = await sociosService.listar({ limit: 100 });
        socios = resSocios.items || [];
        store.setSocios(socios);
      } catch (e) {
        console.warn(e);
      }
    }

    let librosDisponibles = [];
    try {
      const resLibros = await librosService.listar({ limit: 100 });
      librosDisponibles = (resLibros.items || []).filter(l => l.disponibles > 0);
    } catch (e) {
      console.warn(e);
    }

    const modalHtml = `
      <div id="modal-prestamo-form" class="fixed inset-0 z-50 flex items-center justify-center p-4 modal-backdrop">
        <div class="bg-ivory rounded-3xl max-w-md w-full p-6 sm:p-8 shadow-2xl border border-parchment-300 modal-content-panel">
          <div class="flex items-center justify-between pb-3 border-b border-parchment-300">
            <div>
              <span class="text-[10px] font-display uppercase tracking-widest text-gold font-bold">Circulación</span>
              <h3 class="font-editorial text-xl font-bold text-forest">Conceder Préstamo</h3>
            </div>
            <button onclick="window.prestamosViewInstance.cerrarModalForm()" class="text-warmgray hover:text-forest text-xl">&times;</button>
          </div>

          <form onsubmit="window.prestamosViewInstance.guardarPrestamo(event)" class="mt-4 space-y-4">
            <div>
              <label class="block text-xs font-bold text-forest mb-1">Socio Solicitante *</label>
              <select id="prestamo-socio-id" required class="w-full px-3 py-2 bg-parchment-50 border border-parchment-300 rounded-xl text-xs text-forest focus:ring-2 focus:ring-forest focus:outline-none">
                <option value="">-- Seleccionar Socio --</option>
                ${socios.map(s => `<option value="${s.id}">${s.nombre} (${s.email})</option>`).join('')}
              </select>
            </div>

            <div>
              <label class="block text-xs font-bold text-forest mb-1">Obra a Prestar (Solo disponibles) *</label>
              <select id="prestamo-libro-id" required class="w-full px-3 py-2 bg-parchment-50 border border-parchment-300 rounded-xl text-xs text-forest focus:ring-2 focus:ring-forest focus:outline-none">
                <option value="">-- Seleccionar Libro --</option>
                ${librosDisponibles.map(l => `
                  <option value="${l.id}" ${preselectedLibroId === l.id ? 'selected' : ''}>
                    ${l.titulo} (${l.disponibles} disp.)
                  </option>
                `).join('')}
              </select>
            </div>

            <div>
              <label class="block text-xs font-bold text-forest mb-1">Plazo de Devolución en Días (1 a 30 días)</label>
              <input type="number" id="prestamo-dias" min="1" max="30" value="14" required class="w-full px-3 py-2 bg-parchment-50 border border-parchment-300 rounded-xl text-xs text-forest focus:ring-2 focus:ring-forest focus:outline-none">
              <span class="text-[11px] text-warmgray mt-1 block">Regla reglamentaria estándar: 14 días corridos.</span>
            </div>

            <div class="pt-4 border-t border-parchment-300 flex justify-end gap-2">
              <button type="button" onclick="window.prestamosViewInstance.cerrarModalForm()" class="px-4 py-2 border border-parchment-300 rounded-xl text-xs font-semibold hover:bg-parchment">Cancelar</button>
              <button type="submit" class="px-5 py-2 bg-forest text-parchment-50 font-bold rounded-xl text-xs shadow-md">Registrar Salida</button>
            </div>
          </form>
        </div>
      </div>
    `;

    document.getElementById('modal-portal').innerHTML = modalHtml;
  },

  async guardarPrestamo(e) {
    e.preventDefault();
    const payload = {
      socio_id: parseInt(document.getElementById('prestamo-socio-id').value),
      libro_id: parseInt(document.getElementById('prestamo-libro-id').value),
      dias: parseInt(document.getElementById('prestamo-dias').value)
    };

    try {
      await prestamosService.crear(payload);
      this.cerrarModalForm();
      UI.toast('Préstamo registrado correctamente');
      this.cargarPrestamos();
    } catch (err) {
      UI.toast(err.message, 'error');
    }
  },

  async registrarDevolucion(prestamoId) {
    const ok = await UI.confirm(
      'Recepción física de la obra',
      '¿Confirmas que el libro ha sido reincorporado a la estantería en buenas condiciones?'
    );
    if (!ok) return;

    try {
      const res = await prestamosService.registrarDevolucion(prestamoId);
      if (res && res.multa > 0) {
        UI.toast(`Devolución fuera de plazo. Se generó multa de $${res.multa}`, 'warning');
      } else {
        UI.toast('Devolución registrada a tiempo');
      }
      this.cargarPrestamos();
    } catch (err) {
      UI.toast(err.message, 'error');
    }
  },

  async pagarMulta(prestamoId) {
    const ok = await UI.confirm('¿Liquidar multa?', '¿Confirmas el pago total de la multa pendiente?');
    if (!ok) return;

    try {
      await prestamosService.pagarMulta(prestamoId);
      UI.toast('Multa saldada con éxito');
      this.cargarPrestamos();
    } catch (err) {
      UI.toast(err.message, 'error');
    }
  },

  cerrarModalForm() {
    document.getElementById('modal-portal').innerHTML = '';
  }
};
