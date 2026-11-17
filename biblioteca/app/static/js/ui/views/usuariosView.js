/**
 * VISTA: ADMINISTRACIÓN DE USUARIOS
 * Exclusiva para administradores. Conecta con /api/v1/usuarios.
 */

import { usuariosService } from '../../services/usuariosService.js';
import { store } from '../../state.js';
import { UI } from '../components.js';

export const usuariosView = {
  skip: 0,
  limit: 15,
  usuarios: [],

  async render(container) {
    const { isAdmin } = store.get();

    if (!isAdmin) {
      container.innerHTML = UI.emptyState(
        'Acceso Restringido a Administradores',
        'La gestión de cuentas de usuario y permisos del sistema requiere el rol de Administrador.'
      );
      return;
    }

    container.innerHTML = `
      <div class="space-y-6 animate-fade-in">

        <div class="flex flex-col md:flex-row md:items-center md:justify-between gap-4 pb-4 border-b border-parchment-300">
          <div>
            <span class="text-xs font-display tracking-widest uppercase text-gold font-bold">Gobernanza del Sistema</span>
            <h2 class="text-2xl sm:text-3xl font-bold font-editorial text-forest">Administración de Usuarios</h2>
            <p class="text-xs text-warmgray mt-1">Gestión de cuentas del personal, asignación de roles y estados de acceso.</p>
          </div>

          <button onclick="window.usuariosViewInstance.abrirModalCrear()" class="inline-flex items-center gap-2 bg-forest hover:bg-forest-light text-parchment-50 font-display uppercase tracking-wider text-xs font-bold px-4 py-2.5 rounded-xl shadow-md transition self-start md:self-auto">
            <i class="fa-solid fa-user-shield text-gold"></i> Crear Usuario Staff
          </button>
        </div>

        <div class="bg-parchment-light rounded-3xl border border-parchment-300 shadow-sm overflow-hidden">
          <div class="overflow-x-auto">
            <table class="min-w-full divide-y divide-parchment-300 text-xs text-left">
              <thead class="bg-parchment-200 text-forest font-display uppercase tracking-wider text-[11px]">
                <tr>
                  <th class="px-5 py-3.5 font-bold">ID</th>
                  <th class="px-5 py-3.5 font-bold">Correo Electrónico</th>
                  <th class="px-5 py-3.5 font-bold">Rol Asignado</th>
                  <th class="px-5 py-3.5 font-bold">Estado</th>
                  <th class="px-5 py-3.5 font-bold">Último Acceso</th>
                  <th class="px-5 py-3.5 font-bold text-right">Acciones</th>
                </tr>
              </thead>
              <tbody id="tabla-usuarios-body" class="divide-y divide-parchment-200 font-sans text-warmgray-dark">
                <tr>
                  <td colspan="6" class="p-8 text-center">${UI.loadingSpinner('Consultando usuarios registrados...')}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <div id="usuarios-paginacion-container"></div>

      </div>
    `;

    window.usuariosViewInstance = this;
    await this.cargarUsuarios();
  },

  async cargarUsuarios() {
    const tbody = document.getElementById('tabla-usuarios-body');
    const pagContainer = document.getElementById('usuarios-paginacion-container');
    if (!tbody) return;

    try {
      const res = await usuariosService.listar({ skip: this.skip, limit: this.limit });
      const usuarios = res.items || [];
      this.usuarios = usuarios;

      const { currentUser } = store.get();

      tbody.innerHTML = usuarios.map(u => {
        const esPropio = currentUser && currentUser.id === u.id;
        const estadoBadge = u.activo
          ? `<span class="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-bold bg-emerald-50 text-emerald-800 border border-emerald-200">Activo</span>`
          : `<span class="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-bold bg-red-50 text-red-800 border border-red-200">Inactivo</span>`;

        return `
          <tr class="hover:bg-parchment-50 transition">
            <td class="px-5 py-3.5 font-mono font-bold text-gold">#${u.id}</td>
            <td class="px-5 py-3.5 font-bold text-forest text-sm font-mono">${u.email} ${esPropio ? '<span class="text-gold text-[10px] ml-1 font-sans">(Tú)</span>' : ''}</td>
            <td class="px-5 py-3.5">${UI.roleBadge(u.rol)}</td>
            <td class="px-5 py-3.5">${estadoBadge}</td>
            <td class="px-5 py-3.5 text-warmgray">${u.ultimo_login ? new Date(u.ultimo_login).toLocaleString() : 'Sin registros'}</td>
            <td class="px-5 py-3.5 text-right space-x-1 whitespace-nowrap">
              ${!esPropio ? `
                <button onclick="window.usuariosViewInstance.cambiarRol(${u.id}, '${u.rol}')" class="px-2.5 py-1 rounded-lg bg-parchment text-forest hover:bg-parchment-200 font-semibold text-[11px] transition">
                  <i class="fa-solid fa-arrows-rotate text-gold text-[10px]"></i> Cambiar Rol
                </button>
                <button onclick="window.usuariosViewInstance.toggleActivo(${u.id}, ${u.activo})" class="px-2.5 py-1 rounded-lg ${u.activo ? 'bg-red-50 text-red-700 hover:bg-red-100' : 'bg-emerald-50 text-emerald-700 hover:bg-emerald-100'} font-semibold text-[11px] transition">
                  ${u.activo ? 'Desactivar' : 'Activar'}
                </button>
              ` : '<span class="text-xs text-warmgray italic">Cuenta actual</span>'}
            </td>
          </tr>
        `;
      }).join('');

      pagContainer.innerHTML = UI.renderPagination(
        res.total,
        this.skip,
        this.limit,
        'window.usuariosViewInstance.cambiarPagina'
      );
    } catch (e) {
      tbody.innerHTML = `<tr><td colspan="6" class="p-8 text-center text-red-800">${e.message}</td></tr>`;
    }
  },

  cambiarPagina(nuevoSkip) {
    this.skip = nuevoSkip;
    this.cargarUsuarios();
  },

  abrirModalCrear() {
    const modalHtml = `
      <div id="modal-usuario-form" class="fixed inset-0 z-50 flex items-center justify-center p-4 modal-backdrop">
        <div class="bg-ivory rounded-3xl max-w-md w-full p-6 sm:p-8 shadow-2xl border border-parchment-300 modal-content-panel">
          <div class="flex items-center justify-between pb-3 border-b border-parchment-300">
            <div>
              <span class="text-[10px] font-display uppercase tracking-widest text-gold font-bold">Personal</span>
              <h3 class="font-editorial text-xl font-bold text-forest">Crear Usuario Staff</h3>
            </div>
            <button onclick="window.usuariosViewInstance.cerrarModalForm()" class="text-warmgray hover:text-forest text-xl">&times;</button>
          </div>

          <form onsubmit="window.usuariosViewInstance.guardarNuevoUsuario(event)" class="mt-4 space-y-4">
            <div>
              <label class="block text-xs font-bold text-forest mb-1">Correo Electrónico *</label>
              <input type="email" id="crear-usuario-email" required placeholder="personal@biblioteca.com" class="w-full px-3 py-2 bg-parchment-50 border border-parchment-300 rounded-xl text-xs text-forest focus:ring-2 focus:ring-forest focus:outline-none">
            </div>

            <div>
              <label class="block text-xs font-bold text-forest mb-1">Contraseña Inicial (mínimo 8 caracteres) *</label>
              <input type="password" id="crear-usuario-password" required minlength="8" placeholder="••••••••" class="w-full px-3 py-2 bg-parchment-50 border border-parchment-300 rounded-xl text-xs text-forest focus:ring-2 focus:ring-forest focus:outline-none">
            </div>

            <div>
              <label class="block text-xs font-bold text-forest mb-1">Rol a Asignar *</label>
              <select id="crear-usuario-rol" required class="w-full px-3 py-2 bg-parchment-50 border border-parchment-300 rounded-xl text-xs text-forest focus:ring-2 focus:ring-forest focus:outline-none">
                <option value="bibliotecario">Bibliotecario (Gestión de catálogo y préstamos)</option>
                <option value="admin">Administrador (Acceso y control total)</option>
              </select>
            </div>

            <div class="pt-4 border-t border-parchment-300 flex justify-end gap-2">
              <button type="button" onclick="window.usuariosViewInstance.cerrarModalForm()" class="px-4 py-2 border border-parchment-300 rounded-xl text-xs font-semibold hover:bg-parchment">Cancelar</button>
              <button type="submit" class="px-5 py-2 bg-forest text-parchment-50 font-bold rounded-xl text-xs shadow-md">Crear Cuenta</button>
            </div>
          </form>
        </div>
      </div>
    `;

    document.getElementById('modal-portal').innerHTML = modalHtml;
  },

  async guardarNuevoUsuario(e) {
    e.preventDefault();
    const payload = {
      email: document.getElementById('crear-usuario-email').value.trim().toLowerCase(),
      password: document.getElementById('crear-usuario-password').value,
      rol: document.getElementById('crear-usuario-rol').value
    };

    try {
      await usuariosService.crear(payload);
      this.cerrarModalForm();
      UI.toast('Usuario creado con éxito');
      this.cargarUsuarios();
    } catch (err) {
      UI.toast(err.message, 'error');
    }
  },

  async cambiarRol(id, rolActual) {
    const nuevoRol = rolActual === 'admin' ? 'bibliotecario' : 'admin';
    const ok = await UI.confirm(
      '¿Modificar privilegios?',
      `¿Deseas cambiar el rol de este usuario a "${nuevoRol.toUpperCase()}"?`
    );
    if (!ok) return;

    try {
      await usuariosService.cambiarRol(id, nuevoRol);
      UI.toast(`Rol cambiado a ${nuevoRol}`);
      this.cargarUsuarios();
    } catch (err) {
      UI.toast(err.message, 'error');
    }
  },

  async toggleActivo(id, estadoActual) {
    const accion = estadoActual ? 'desactivar' : 'activar';
    const ok = await UI.confirm(
      `¿Confirmar ${accion}?`,
      `¿Deseas ${accion} esta cuenta de usuario?`,
      'Confirmar',
      estadoActual
    );
    if (!ok) return;

    try {
      await usuariosService.cambiarActivo(id, !estadoActual);
      UI.toast(`Usuario ${!estadoActual ? 'activado' : 'desactivado'}`);
      this.cargarUsuarios();
    } catch (err) {
      UI.toast(err.message, 'error');
    }
  },

  cerrarModalForm() {
    document.getElementById('modal-portal').innerHTML = '';
  }
};
