/**
 * VISTA: AUTORES
 * Directorio biográfico y editorial de autores literarios.
 */

import { autoresService } from '../../services/autoresService.js';
import { librosService } from '../../services/librosService.js';
import { store } from '../../state.js';
import { UI } from '../components.js';

export const autoresView = {
  skip: 0,
  limit: 12,
  nacionalidadFiltro: '',
  autores: [],

  async render(container) {
    const { isStaff, isAdmin } = store.get();

    container.innerHTML = `
      <div class="space-y-6 animate-fade-in">

        <div class="flex flex-col md:flex-row md:items-center md:justify-between gap-4 pb-4 border-b border-parchment-300">
          <div>
            <span class="text-xs font-display tracking-widest uppercase text-gold font-bold">Biografías Literarias</span>
            <h2 class="text-2xl sm:text-3xl font-bold font-editorial text-forest">Directorio de Autores</h2>
            <p class="text-xs text-warmgray mt-1">Creadores, ensayistas y novelistas presentes en el acervo de la biblioteca.</p>
          </div>

          ${isStaff ? `
            <button onclick="window.autoresViewInstance.abrirModalCrear()" class="inline-flex items-center gap-2 bg-forest hover:bg-forest-light text-parchment-50 font-display uppercase tracking-wider text-xs font-bold px-4 py-2.5 rounded-xl shadow-md transition self-start md:self-auto">
              <i class="fa-solid fa-plus text-gold"></i> Registrar Autor
            </button>
          ` : ''}
        </div>

        <div id="autores-lista-container">
          ${UI.loadingSpinner('Consultando registros biográficos...')}
        </div>

        <div id="autores-paginacion-container"></div>

      </div>
    `;

    window.autoresViewInstance = this;
    await this.cargarAutores();
  },

  async cargarAutores() {
    const listContainer = document.getElementById('autores-lista-container');
    const pagContainer = document.getElementById('autores-paginacion-container');
    if (!listContainer) return;

    listContainer.innerHTML = UI.loadingSpinner('Cargando catálogo de autores...');

    try {
      const res = await autoresService.listar({
        skip: this.skip,
        limit: this.limit,
        nacionalidad: this.nacionalidadFiltro || null
      });

      const autores = res.items || [];
      this.autores = autores;

      if (autores.length === 0) {
        listContainer.innerHTML = UI.emptyState(
          'No se registran autores',
          'Añade nuevos autores literarios para vincularlos con las obras.',
          store.get().isStaff ? 'Registrar Autor' : null,
          'window.autoresViewInstance.abrirModalCrear()'
        );
        pagContainer.innerHTML = '';
        return;
      }

      const { isStaff, isAdmin } = store.get();

      listContainer.innerHTML = `
        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-5">
          ${autores.map(a => `
            <div class="bg-parchment-light rounded-3xl border border-parchment-300 p-5 shadow-sm hover:shadow-md transition flex flex-col justify-between book-spine-card">
              <div>
                <div class="flex items-center justify-between text-gold mb-3">
                  <div class="w-10 h-10 rounded-2xl bg-parchment-200 border border-parchment-300 flex items-center justify-center text-forest">
                    <i class="fa-solid fa-feather-pointed text-base"></i>
                  </div>
                  <span class="text-[10px] font-mono font-bold text-warmgray">#${a.id}</span>
                </div>

                <h3 class="font-editorial text-lg font-bold text-forest leading-snug line-clamp-1" title="${a.nombre}">
                  ${a.nombre}
                </h3>

                <div class="mt-2 space-y-1 text-xs text-warmgray-dark">
                  <p class="flex items-center gap-1.5">
                    <i class="fa-solid fa-earth-americas text-gold text-[11px]"></i>
                    <span>${a.nacionalidad || '<em class="text-warmgray">Nacionalidad no registrada</em>'}</span>
                  </p>
                  <p class="flex items-center gap-1.5">
                    <i class="fa-solid fa-calendar text-gold text-[11px]"></i>
                    <span>Nacimiento: ${a.anio_nacimiento || '<em class="text-warmgray">Año desconocido</em>'}</span>
                  </p>
                </div>
              </div>

              <div class="mt-5 pt-3 border-t border-parchment-300 flex items-center justify-between gap-2">
                <button onclick="window.autoresViewInstance.verLibrosDeAutor(${a.id}, '${a.nombre.replace(/'/g, "\\'")}')" class="text-xs font-semibold text-forest hover:text-gold flex items-center gap-1 font-display uppercase tracking-wider">
                  <i class="fa-solid fa-book-open text-[10px]"></i> Ver Obras
                </button>

                <div class="flex items-center gap-1">
                  ${isStaff ? `
                    <button onclick="window.autoresViewInstance.abrirModalEditar(${a.id})" title="Editar Autor" class="w-7 h-7 rounded-lg text-warmgray hover:text-forest hover:bg-parchment flex items-center justify-center transition text-xs">
                      <i class="fa-solid fa-pen-to-square"></i>
                    </button>
                  ` : ''}

                  ${isAdmin ? `
                    <button onclick="window.autoresViewInstance.eliminarAutor(${a.id}, '${a.nombre.replace(/'/g, "\\'")}')" title="Eliminar Autor" class="w-7 h-7 rounded-lg text-warmgray hover:text-red-700 hover:bg-red-50 flex items-center justify-center transition text-xs">
                      <i class="fa-solid fa-trash-can"></i>
                    </button>
                  ` : ''}
                </div>
              </div>
            </div>
          `).join('')}
        </div>
      `;

      pagContainer.innerHTML = UI.renderPagination(
        res.total,
        this.skip,
        this.limit,
        'window.autoresViewInstance.cambiarPagina'
      );
    } catch (e) {
      listContainer.innerHTML = UI.emptyState('Error cargando autores', e.message);
    }
  },

  cambiarPagina(nuevoSkip) {
    this.skip = nuevoSkip;
    this.cargarAutores();
    window.scrollTo({ top: 200, behavior: 'smooth' });
  },

  abrirModalCrear() {
    const modalHtml = `
      <div id="modal-autor-form" class="fixed inset-0 z-50 flex items-center justify-center p-4 modal-backdrop">
        <div class="bg-ivory rounded-3xl max-w-md w-full p-6 sm:p-8 shadow-2xl border border-parchment-300 modal-content-panel">
          <div class="flex items-center justify-between pb-3 border-b border-parchment-300">
            <div>
              <span class="text-[10px] font-display uppercase tracking-widest text-gold font-bold">Autoría</span>
              <h3 class="font-editorial text-xl font-bold text-forest">Registrar Autor</h3>
            </div>
            <button onclick="window.autoresViewInstance.cerrarModalForm()" class="text-warmgray hover:text-forest text-xl">&times;</button>
          </div>

          <form onsubmit="window.autoresViewInstance.guardarNuevoAutor(event)" class="mt-4 space-y-4">
            <div>
              <label class="block text-xs font-bold text-forest mb-1">Nombre Completo *</label>
              <input type="text" id="crear-autor-nombre" required placeholder="Ej: Gabriel García Márquez" class="w-full px-3 py-2 bg-parchment-50 border border-parchment-300 rounded-xl text-xs text-forest focus:ring-2 focus:ring-forest focus:outline-none">
            </div>

            <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div>
                <label class="block text-xs font-bold text-forest mb-1">Nacionalidad</label>
                <input type="text" id="crear-autor-nacionalidad" placeholder="Ej: Colombiana" class="w-full px-3 py-2 bg-parchment-50 border border-parchment-300 rounded-xl text-xs text-forest focus:ring-2 focus:ring-forest focus:outline-none">
              </div>
              <div>
                <label class="block text-xs font-bold text-forest mb-1">Año de Nacimiento</label>
                <input type="number" id="crear-autor-anio" min="1000" max="${new Date().getFullYear()}" placeholder="1927" class="w-full px-3 py-2 bg-parchment-50 border border-parchment-300 rounded-xl text-xs text-forest focus:ring-2 focus:ring-forest focus:outline-none">
              </div>
            </div>

            <div class="pt-4 border-t border-parchment-300 flex justify-end gap-2">
              <button type="button" onclick="window.autoresViewInstance.cerrarModalForm()" class="px-4 py-2 border border-parchment-300 rounded-xl text-xs font-semibold hover:bg-parchment">Cancelar</button>
              <button type="submit" class="px-5 py-2 bg-forest text-parchment-50 font-bold rounded-xl text-xs shadow-md">Guardar</button>
            </div>
          </form>
        </div>
      </div>
    `;

    document.getElementById('modal-portal').innerHTML = modalHtml;
  },

  async guardarNuevoAutor(e) {
    e.preventDefault();
    const anioVal = document.getElementById('crear-autor-anio').value;
    const payload = {
      nombre: document.getElementById('crear-autor-nombre').value.trim(),
      nacionalidad: document.getElementById('crear-autor-nacionalidad').value.trim() || null,
      anio_nacimiento: anioVal ? parseInt(anioVal) : null
    };

    try {
      await autoresService.crear(payload);
      this.cerrarModalForm();
      UI.toast('Autor registrado exitosamente');
      this.cargarAutores();
    } catch (err) {
      UI.toast(err.message, 'error');
    }
  },

  abrirModalEditar(id) {
    const autor = this.autores.find(a => a.id === id);
    if (!autor) return;

    const modalHtml = `
      <div id="modal-autor-form" class="fixed inset-0 z-50 flex items-center justify-center p-4 modal-backdrop">
        <div class="bg-ivory rounded-3xl max-w-md w-full p-6 sm:p-8 shadow-2xl border border-parchment-300 modal-content-panel">
          <div class="flex items-center justify-between pb-3 border-b border-parchment-300">
            <div>
              <span class="text-[10px] font-display uppercase tracking-widest text-gold font-bold">Edición</span>
              <h3 class="font-editorial text-xl font-bold text-forest">Editar Autor</h3>
            </div>
            <button onclick="window.autoresViewInstance.cerrarModalForm()" class="text-warmgray hover:text-forest text-xl">&times;</button>
          </div>

          <form onsubmit="window.autoresViewInstance.guardarEdicionAutor(event, ${autor.id})" class="mt-4 space-y-4">
            <div>
              <label class="block text-xs font-bold text-forest mb-1">Nombre Completo *</label>
              <input type="text" id="editar-autor-nombre" required value="${autor.nombre}" class="w-full px-3 py-2 bg-parchment-50 border border-parchment-300 rounded-xl text-xs text-forest focus:ring-2 focus:ring-forest focus:outline-none">
            </div>

            <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div>
                <label class="block text-xs font-bold text-forest mb-1">Nacionalidad</label>
                <input type="text" id="editar-autor-nacionalidad" value="${autor.nacionalidad || ''}" class="w-full px-3 py-2 bg-parchment-50 border border-parchment-300 rounded-xl text-xs text-forest focus:ring-2 focus:ring-forest focus:outline-none">
              </div>
              <div>
                <label class="block text-xs font-bold text-forest mb-1">Año de Nacimiento</label>
                <input type="number" id="editar-autor-anio" min="1000" max="${new Date().getFullYear()}" value="${autor.anio_nacimiento || ''}" class="w-full px-3 py-2 bg-parchment-50 border border-parchment-300 rounded-xl text-xs text-forest focus:ring-2 focus:ring-forest focus:outline-none">
              </div>
            </div>

            <div class="pt-4 border-t border-parchment-300 flex justify-end gap-2">
              <button type="button" onclick="window.autoresViewInstance.cerrarModalForm()" class="px-4 py-2 border border-parchment-300 rounded-xl text-xs font-semibold hover:bg-parchment">Cancelar</button>
              <button type="submit" class="px-5 py-2 bg-forest text-parchment-50 font-bold rounded-xl text-xs shadow-md">Actualizar</button>
            </div>
          </form>
        </div>
      </div>
    `;

    document.getElementById('modal-portal').innerHTML = modalHtml;
  },

  async guardarEdicionAutor(e, id) {
    e.preventDefault();
    const anioVal = document.getElementById('editar-autor-anio').value;
    const payload = {
      nombre: document.getElementById('editar-autor-nombre').value.trim(),
      nacionalidad: document.getElementById('editar-autor-nacionalidad').value.trim() || null,
      anio_nacimiento: anioVal ? parseInt(anioVal) : null
    };

    try {
      await autoresService.actualizar(id, payload);
      this.cerrarModalForm();
      UI.toast('Autor actualizado');
      this.cargarAutores();
    } catch (err) {
      UI.toast(err.message, 'error');
    }
  },

  cerrarModalForm() {
    document.getElementById('modal-portal').innerHTML = '';
  },

  async eliminarAutor(id, nombre) {
    const ok = await UI.confirm('¿Dar de baja autor?', `¿Deseas eliminar a "${nombre}" del catálogo?`, 'Eliminar', true);
    if (!ok) return;

    try {
      await autoresService.eliminar(id);
      UI.toast('Autor eliminado');
      this.cargarAutores();
    } catch (err) {
      UI.toast(err.message, 'error');
    }
  },

  async verLibrosDeAutor(autorId, nombreAutor) {
    try {
      const res = await librosService.librosDeAutor(autorId, 0, 50);
      const libros = res.items || [];

      const modalHtml = `
        <div id="modal-autor-libros" class="fixed inset-0 z-50 flex items-center justify-center p-4 modal-backdrop">
          <div class="bg-ivory rounded-3xl max-w-lg w-full p-6 sm:p-8 shadow-2xl border border-parchment-300 max-h-[85vh] overflow-y-auto modal-content-panel">
            <div class="flex items-center justify-between pb-3 border-b border-parchment-300">
              <div>
                <span class="text-[10px] font-display uppercase tracking-widest text-gold font-bold">Bibliografía</span>
                <h3 class="font-editorial text-xl font-bold text-forest">Obras de ${nombreAutor}</h3>
              </div>
              <button onclick="window.autoresViewInstance.cerrarModalForm()" class="text-warmgray hover:text-forest text-xl">&times;</button>
            </div>

            <div class="mt-4 space-y-3">
              ${libros.length > 0 ? libros.map(l => `
                <div class="p-3 bg-parchment-50 rounded-2xl border border-parchment-300 flex items-center justify-between">
                  <div>
                    <h4 class="font-editorial text-sm font-bold text-forest">${l.titulo}</h4>
                    <p class="text-[11px] text-warmgray">Año: ${l.anio_publicacion} · Ejemplares: ${l.disponibles} de ${l.ejemplares} disp.</p>
                  </div>
                  <span class="text-xs font-mono font-bold text-gold">ISBN ${l.isbn}</span>
                </div>
              `).join('') : '<p class="text-center py-6 text-xs text-warmgray">No se han registrado obras vinculadas a este autor aún.</p>'}
            </div>

            <div class="mt-5 pt-3 border-t border-parchment-300 flex justify-end">
              <button onclick="window.autoresViewInstance.cerrarModalForm()" class="px-4 py-1.5 bg-forest text-parchment-50 rounded-xl text-xs font-semibold">Cerrar</button>
            </div>
          </div>
        </div>
      `;

      document.getElementById('modal-portal').innerHTML = modalHtml;
    } catch (err) {
      UI.toast(err.message, 'error');
    }
  }
};
