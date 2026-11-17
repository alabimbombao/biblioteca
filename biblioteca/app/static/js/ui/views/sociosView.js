/**
 * VISTA: SOCIOS
 * Directorio de miembros y gestión de credenciales lectoras.
 */

import { sociosService } from '../../services/sociosService.js';
import { store } from '../../state.js';
import { UI } from '../components.js';

export const sociosView = {
  skip: 0,
  limit: 15,
  filtroActivo: '',
  socios: [],

  async render(container) {
    const { currentUser, isStaff, isSocio } = store.get();

    if (!currentUser) {
      container.innerHTML = UI.emptyState(
        'Acceso Restringido a Socios y Personal',
        'Inicia sesión con tu cuenta de socio o del personal bibliotecario para consultar los registros y credenciales.',
        'Iniciar Sesión',
        'window.appRouter.abrirModalLogin()'
      );
      return;
    }

    // Si es un Socio autenticado, mostrar su perfil personal y sus préstamos
    if (isSocio && !isStaff) {
      await this.renderPerfilPropio(container);
      return;
    }

    // Vista de Staff (Bibliotecario y Admin): Directorio completo
    container.innerHTML = `
      <div class="space-y-6 animate-fade-in">

        <div class="flex flex-col md:flex-row md:items-center md:justify-between gap-4 pb-4 border-b border-parchment-300">
          <div>
            <span class="text-xs font-display tracking-widest uppercase text-gold font-bold">Padrón de Lectores</span>
            <h2 class="text-2xl sm:text-3xl font-bold font-editorial text-forest">Directorio de Socios</h2>
            <p class="text-xs text-warmgray mt-1">Usuarios autorizados para el préstamo domiciliario de obras.</p>
          </div>

          <button onclick="window.sociosViewInstance.abrirModalCrear()" class="inline-flex items-center gap-2 bg-forest hover:bg-forest-light text-parchment-50 font-display uppercase tracking-wider text-xs font-bold px-4 py-2.5 rounded-xl shadow-md transition self-start md:self-auto">
            <i class="fa-solid fa-user-plus text-gold"></i> Afiliar Nuevo Socio
          </button>
        </div>

        <div class="bg-parchment-light rounded-3xl border border-parchment-300 shadow-sm overflow-hidden">
          <div class="overflow-x-auto">
            <table class="min-w-full divide-y divide-parchment-300 text-xs text-left">
              <thead class="bg-parchment-200 text-forest font-display uppercase tracking-wider text-[11px]">
                <tr>
                  <th class="px-5 py-3.5 font-bold">Credencial</th>
                  <th class="px-5 py-3.5 font-bold">Nombre Completo</th>
                  <th class="px-5 py-3.5 font-bold">Correo Electrónico</th>
                  <th class="px-5 py-3.5 font-bold">Teléfono</th>
                  <th class="px-5 py-3.5 font-bold">Fecha Registro</th>
                  <th class="px-5 py-3.5 font-bold text-right">Acciones</th>
                </tr>
              </thead>
              <tbody id="tabla-socios-body" class="divide-y divide-parchment-200 font-sans text-warmgray-dark">
                <tr>
                  <td colspan="6" class="p-8 text-center">${UI.loadingSpinner('Consultando padrón...')}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <div id="socios-paginacion-container"></div>

      </div>
    `;

    window.sociosViewInstance = this;
    await this.cargarSocios();
  },

  async cargarSocios() {
    const tbody = document.getElementById('tabla-socios-body');
    const pagContainer = document.getElementById('socios-paginacion-container');
    if (!tbody) return;

    try {
      const res = await sociosService.listar({
        skip: this.skip,
        limit: this.limit,
        activo: this.filtroActivo !== '' ? this.filtroActivo === 'true' : null
      });

      const socios = res.items || [];
      this.socios = socios;
      store.setSocios(socios);

      if (socios.length === 0) {
        tbody.innerHTML = `<tr><td colspan="6" class="p-8 text-center text-warmgray">No hay socios registrados bajo los filtros actuales.</td></tr>`;
        pagContainer.innerHTML = '';
        return;
      }

      const { isAdmin } = store.get();

      tbody.innerHTML = socios.map(s => `
        <tr class="hover:bg-parchment-50 transition">
          <td class="px-5 py-3.5 font-mono font-bold text-gold">#${s.id}</td>
          <td class="px-5 py-3.5 font-editorial font-bold text-forest text-sm">${s.nombre}</td>
          <td class="px-5 py-3.5 font-mono text-warmgray">${s.email}</td>
          <td class="px-5 py-3.5">${s.telefono || '<em class="text-warmgray">Sin teléfono</em>'}</td>
          <td class="px-5 py-3.5 text-warmgray">${s.fecha_alta ? new Date(s.fecha_alta).toLocaleDateString() : 'N/A'}</td>
          <td class="px-5 py-3.5 text-right space-x-1 whitespace-nowrap">
            <button onclick="window.sociosViewInstance.verPrestamosSocio(${s.id}, '${s.nombre.replace(/'/g, "\\'")}')" class="px-2.5 py-1 rounded-lg bg-parchment text-forest hover:bg-parchment-200 font-semibold text-[11px] transition">
              <i class="fa-solid fa-receipt text-gold"></i> Préstamos
            </button>
            <button onclick="window.sociosViewInstance.abrirModalEditar(${s.id})" class="p-1.5 rounded-lg text-warmgray hover:text-forest hover:bg-parchment transition">
              <i class="fa-solid fa-pen-to-square"></i>
            </button>
            ${isAdmin ? `
              <button onclick="window.sociosViewInstance.eliminarSocio(${s.id}, '${s.nombre.replace(/'/g, "\\'")}')" class="p-1.5 rounded-lg text-warmgray hover:text-red-700 hover:bg-red-50 transition">
                <i class="fa-solid fa-trash-can"></i>
              </button>
            ` : ''}
          </td>
        </tr>
      `).join('');

      pagContainer.innerHTML = UI.renderPagination(
        res.total,
        this.skip,
        this.limit,
        'window.sociosViewInstance.cambiarPagina'
      );
    } catch (e) {
      tbody.innerHTML = `<tr><td colspan="6" class="p-8 text-center text-red-800">${e.message}</td></tr>`;
    }
  },

  cambiarPagina(nuevoSkip) {
    this.skip = nuevoSkip;
    this.cargarSocios();
  },

  abrirModalCrear() {
    const modalHtml = `
      <div id="modal-socio-form" class="fixed inset-0 z-50 flex items-center justify-center p-4 modal-backdrop">
        <div class="bg-ivory rounded-3xl max-w-md w-full p-6 sm:p-8 shadow-2xl border border-parchment-300 modal-content-panel">
          <div class="flex items-center justify-between pb-3 border-b border-parchment-300">
            <div>
              <span class="text-[10px] font-display uppercase tracking-widest text-gold font-bold">Afiliación</span>
              <h3 class="font-editorial text-xl font-bold text-forest">Nuevo Socio Lector</h3>
            </div>
            <button onclick="window.sociosViewInstance.cerrarModalForm()" class="text-warmgray hover:text-forest text-xl">&times;</button>
          </div>

          <form onsubmit="window.sociosViewInstance.guardarNuevoSocio(event)" class="mt-4 space-y-4">
            <div>
              <label class="block text-xs font-bold text-forest mb-1">Nombre Completo *</label>
              <input type="text" id="crear-socio-nombre" required placeholder="Ej: Ana Torres" class="w-full px-3 py-2 bg-parchment-50 border border-parchment-300 rounded-xl text-xs text-forest focus:ring-2 focus:ring-forest focus:outline-none">
            </div>

            <div>
              <label class="block text-xs font-bold text-forest mb-1">Correo Electrónico Único *</label>
              <input type="email" id="crear-socio-email" required placeholder="socio@ejemplo.com" class="w-full px-3 py-2 bg-parchment-50 border border-parchment-300 rounded-xl text-xs text-forest focus:ring-2 focus:ring-forest focus:outline-none">
            </div>

            <div>
              <label class="block text-xs font-bold text-forest mb-1">Teléfono (7 a 15 dígitos con +)</label>
              <input type="text" id="crear-socio-telefono" placeholder="+57 3001234567" class="w-full px-3 py-2 bg-parchment-50 border border-parchment-300 rounded-xl text-xs text-forest focus:ring-2 focus:ring-forest focus:outline-none">
            </div>

            <div class="pt-4 border-t border-parchment-300 flex justify-end gap-2">
              <button type="button" onclick="window.sociosViewInstance.cerrarModalForm()" class="px-4 py-2 border border-parchment-300 rounded-xl text-xs font-semibold hover:bg-parchment">Cancelar</button>
              <button type="submit" class="px-5 py-2 bg-forest text-parchment-50 font-bold rounded-xl text-xs shadow-md">Afiliar Socio</button>
            </div>
          </form>
        </div>
      </div>
    `;

    document.getElementById('modal-portal').innerHTML = modalHtml;
  },

  async guardarNuevoSocio(e) {
    e.preventDefault();
    const payload = {
      nombre: document.getElementById('crear-socio-nombre').value.trim(),
      email: document.getElementById('crear-socio-email').value.trim().toLowerCase(),
      telefono: document.getElementById('crear-socio-telefono').value.trim() || null
    };

    try {
      await sociosService.crear(payload);
      this.cerrarModalForm();
      UI.toast('Socio afiliado con éxito');
      this.cargarSocios();
    } catch (err) {
      UI.toast(err.message, 'error');
    }
  },

  abrirModalEditar(id) {
    const s = this.socios.find(item => item.id === id);
    if (!s) return;

    const modalHtml = `
      <div id="modal-socio-form" class="fixed inset-0 z-50 flex items-center justify-center p-4 modal-backdrop">
        <div class="bg-ivory rounded-3xl max-w-md w-full p-6 sm:p-8 shadow-2xl border border-parchment-300 modal-content-panel">
          <div class="flex items-center justify-between pb-3 border-b border-parchment-300">
            <div>
              <span class="text-[10px] font-display uppercase tracking-widest text-gold font-bold">Ficha</span>
              <h3 class="font-editorial text-xl font-bold text-forest">Actualizar Socio</h3>
            </div>
            <button onclick="window.sociosViewInstance.cerrarModalForm()" class="text-warmgray hover:text-forest text-xl">&times;</button>
          </div>

          <form onsubmit="window.sociosViewInstance.guardarEdicionSocio(event, ${s.id})" class="mt-4 space-y-4">
            <div>
              <label class="block text-xs font-bold text-forest mb-1">Nombre Completo</label>
              <input type="text" id="editar-socio-nombre" value="${s.nombre}" class="w-full px-3 py-2 bg-parchment-50 border border-parchment-300 rounded-xl text-xs text-forest focus:ring-2 focus:ring-forest focus:outline-none">
            </div>

            <div>
              <label class="block text-xs font-bold text-forest mb-1">Correo Electrónico (Inmutable)</label>
              <input type="email" disabled value="${s.email}" class="w-full px-3 py-2 bg-parchment-200 border border-parchment-300 rounded-xl text-xs text-warmgray cursor-not-allowed">
            </div>

            <div>
              <label class="block text-xs font-bold text-forest mb-1">Teléfono</label>
              <input type="text" id="editar-socio-telefono" value="${s.telefono || ''}" class="w-full px-3 py-2 bg-parchment-50 border border-parchment-300 rounded-xl text-xs text-forest focus:ring-2 focus:ring-forest focus:outline-none">
            </div>

            <div class="pt-4 border-t border-parchment-300 flex justify-end gap-2">
              <button type="button" onclick="window.sociosViewInstance.cerrarModalForm()" class="px-4 py-2 border border-parchment-300 rounded-xl text-xs font-semibold hover:bg-parchment">Cancelar</button>
              <button type="submit" class="px-5 py-2 bg-forest text-parchment-50 font-bold rounded-xl text-xs shadow-md">Guardar Cambios</button>
            </div>
          </form>
        </div>
      </div>
    `;

    document.getElementById('modal-portal').innerHTML = modalHtml;
  },

  async guardarEdicionSocio(e, id) {
    e.preventDefault();
    const payload = {
      nombre: document.getElementById('editar-socio-nombre').value.trim() || undefined,
      telefono: document.getElementById('editar-socio-telefono').value.trim() || null
    };

    try {
      await sociosService.actualizar(id, payload);
      this.cerrarModalForm();
      UI.toast('Socio actualizado');
      this.cargarSocios();
    } catch (err) {
      UI.toast(err.message, 'error');
    }
  },

  cerrarModalForm() {
    document.getElementById('modal-portal').innerHTML = '';
  },

  async eliminarSocio(id, nombre) {
    const ok = await UI.confirm('¿Dar de baja socio?', `¿Deseas dar de baja la credencial de "${nombre}"?`, 'Dar de baja', true);
    if (!ok) return;

    try {
      await sociosService.eliminar(id);
      UI.toast('Socio dado de baja');
      this.cargarSocios();
    } catch (err) {
      UI.toast(err.message, 'error');
    }
  },

  async verPrestamosSocio(socioId, nombreSocio) {
    try {
      const res = await sociosService.prestamosDeSocio(socioId, 0, 50);
      const prestamos = res.items || [];

      const modalHtml = `
        <div id="modal-socio-prestamos" class="fixed inset-0 z-50 flex items-center justify-center p-4 modal-backdrop">
          <div class="bg-ivory rounded-3xl max-w-lg w-full p-6 sm:p-8 shadow-2xl border border-parchment-300 max-h-[85vh] overflow-y-auto modal-content-panel">
            <div class="flex items-center justify-between pb-3 border-b border-parchment-300">
              <div>
                <span class="text-[10px] font-display uppercase tracking-widest text-gold font-bold">Circulación</span>
                <h3 class="font-editorial text-xl font-bold text-forest">Préstamos de ${nombreSocio}</h3>
              </div>
              <button onclick="window.sociosViewInstance.cerrarModalForm()" class="text-warmgray hover:text-forest text-xl">&times;</button>
            </div>

            <div class="mt-4 space-y-3">
              ${prestamos.length > 0 ? prestamos.map(p => `
                <div class="p-3 bg-parchment-50 rounded-2xl border border-parchment-300 flex items-center justify-between">
                  <div>
                    <h4 class="font-editorial text-sm font-bold text-forest">${p.libro ? p.libro.titulo : 'Libro #' + p.libro_id}</h4>
                    <p class="text-[11px] text-warmgray">Fecha límite: <strong>${p.fecha_limite}</strong></p>
                  </div>
                  <div class="text-right">
                    ${UI.loanBadge(p.estado)}
                    ${p.multa > 0 ? `<p class="text-[10px] font-bold text-red-600 mt-1">Multa: $${p.multa}</p>` : ''}
                  </div>
                </div>
              `).join('') : '<p class="text-center py-6 text-xs text-warmgray">No registra préstamos en el historial.</p>'}
            </div>

            <div class="mt-5 pt-3 border-t border-parchment-300 flex justify-end">
              <button onclick="window.sociosViewInstance.cerrarModalForm()" class="px-4 py-1.5 bg-forest text-parchment-50 rounded-xl text-xs font-semibold">Cerrar</button>
            </div>
          </div>
        </div>
      `;

      document.getElementById('modal-portal').innerHTML = modalHtml;
    } catch (err) {
      UI.toast(err.message, 'error');
    }
  },

  // Vista para el socio autenticado
  async renderPerfilPropio(container) {
    try {
      const [perfil, prestamos, multas] = await Promise.all([
        sociosService.miPerfil(),
        sociosService.misPrestamos(0, 50),
        sociosService.misMultas()
      ]);

      container.innerHTML = `
        <div class="space-y-6 animate-fade-in max-w-4xl mx-auto">
          
          <div class="bg-parchment-light p-6 sm:p-8 rounded-3xl border border-parchment-300 shadow-sm flex flex-col sm:flex-row items-center gap-6">
            <div class="w-20 h-20 rounded-2xl bg-forest text-parchment-50 flex items-center justify-center text-3xl shadow-md border border-gold">
              <i class="fa-solid fa-address-card text-gold"></i>
            </div>
            <div class="flex-1 text-center sm:text-left">
              <span class="text-xs font-display tracking-widest uppercase text-gold font-bold">Credencial de Lector</span>
              <h2 class="text-2xl font-bold font-editorial text-forest">${perfil.nombre}</h2>
              <p class="text-xs text-warmgray font-mono mt-0.5">${perfil.email} · Tel: ${perfil.telefono || 'No registrado'}</p>
              <p class="text-[11px] text-warmgray mt-1">Afiliado desde: ${perfil.fecha_alta ? new Date(perfil.fecha_alta).toLocaleDateString() : 'N/A'}</p>
            </div>
            <div class="text-right bg-ivory p-4 rounded-2xl border border-parchment-300">
              <span class="text-[11px] font-bold uppercase tracking-wider text-warmgray block">Multas pendientes</span>
              <span class="text-2xl font-bold font-editorial ${multas.total_adeudado > 0 ? 'text-red-700' : 'text-emerald-700'}">
                $${parseFloat(multas.total_adeudado || 0).toFixed(2)}
              </span>
            </div>
          </div>

          <div class="bg-parchment-light p-6 rounded-3xl border border-parchment-300 shadow-sm">
            <h3 class="font-editorial text-lg font-bold text-forest mb-4">Mis Préstamos en Curso e Históricos</h3>
            <div class="space-y-3">
              ${prestamos.items && prestamos.items.length > 0 ? prestamos.items.map(p => `
                <div class="p-4 bg-ivory rounded-2xl border border-parchment-300 flex items-center justify-between">
                  <div>
                    <h4 class="font-editorial text-base font-bold text-forest">${p.libro ? p.libro.titulo : 'Libro #' + p.libro_id}</h4>
                    <p class="text-xs text-warmgray">Préstamo: ${p.fecha_prestamo} · Plazo de devolución: <strong>${p.fecha_limite}</strong></p>
                  </div>
                  <div class="text-right">
                    ${UI.loanBadge(p.estado)}
                    ${p.multa > 0 ? `<p class="text-xs font-bold text-red-600 mt-1">Multa: $${p.multa} ${p.multa_pagada ? '(Pagada)' : '(Pendiente)'}</p>` : ''}
                  </div>
                </div>
              `).join('') : '<p class="text-center py-8 text-xs text-warmgray">No tienes préstamos registrados actualmente.</p>'}
            </div>
          </div>

        </div>
      `;
    } catch (e) {
      container.innerHTML = UI.emptyState('Error cargando tu perfil', e.message);
    }
  }
};
