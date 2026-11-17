/**
 * VISTA: CATEGORÍAS
 * Taxonomía literaria, géneros y clasificación temática.
 */

import { categoriasService } from '../../services/categoriasService.js';
import { store } from '../../state.js';
import { UI } from '../components.js';

export const categoriasView = {
  skip: 0,
  limit: 20,
  categorias: [],

  async render(container) {
    const { isStaff } = store.get();

    container.innerHTML = `
      <div class="space-y-6 animate-fade-in">

        <div class="flex flex-col md:flex-row md:items-center md:justify-between gap-4 pb-4 border-b border-parchment-300">
          <div>
            <span class="text-xs font-display tracking-widest uppercase text-gold font-bold">Taxonomía Literaria</span>
            <h2 class="text-2xl sm:text-3xl font-bold font-editorial text-forest">Géneros y Categorías</h2>
            <p class="text-xs text-warmgray mt-1">Clasificación temática de las obras del catálogo bibliográfico.</p>
          </div>

          ${isStaff ? `
            <button onclick="window.categoriasViewInstance.abrirModalCrear()" class="inline-flex items-center gap-2 bg-forest hover:bg-forest-light text-parchment-50 font-display uppercase tracking-wider text-xs font-bold px-4 py-2.5 rounded-xl shadow-md transition self-start md:self-auto">
              <i class="fa-solid fa-plus text-gold"></i> Nueva Categoría
            </button>
          ` : ''}
        </div>

        <div id="categorias-lista-container">
          ${UI.loadingSpinner('Cargando géneros y materias...')}
        </div>

        <div id="categorias-paginacion-container"></div>

      </div>
    `;

    window.categoriasViewInstance = this;
    await this.cargarCategorias();
  },

  async cargarCategorias() {
    const listContainer = document.getElementById('categorias-lista-container');
    const pagContainer = document.getElementById('categorias-paginacion-container');
    if (!listContainer) return;

    listContainer.innerHTML = UI.loadingSpinner('Consultando materias...');

    try {
      const res = await categoriasService.listar({ skip: this.skip, limit: this.limit });
      const categorias = res.items || [];
      this.categorias = categorias;

      if (categorias.length === 0) {
        listContainer.innerHTML = UI.emptyState(
          'No hay categorías creadas',
          'Crea categorías para organizar los libros en géneros temáticos.',
          store.get().isStaff ? 'Nueva Categoría' : null,
          'window.categoriasViewInstance.abrirModalCrear()'
        );
        pagContainer.innerHTML = '';
        return;
      }

      const { isStaff, isAdmin } = store.get();

      listContainer.innerHTML = `
        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
          ${categorias.map(c => `
            <div class="bg-parchment-light rounded-3xl border border-parchment-300 p-5 shadow-sm hover:shadow-md transition flex flex-col justify-between book-spine-card">
              <div>
                <div class="flex items-center justify-between mb-3">
                  <span class="w-8 h-8 rounded-xl bg-parchment-200 text-forest flex items-center justify-center text-xs">
                    <i class="fa-solid fa-tag text-gold"></i>
                  </span>
                  <span class="text-[10px] font-mono font-bold text-warmgray">#${c.id}</span>
                </div>

                <h3 class="font-editorial text-lg font-bold text-forest capitalize">
                  ${c.nombre}
                </h3>

                <p class="mt-2 text-xs text-warmgray-dark leading-relaxed font-sans line-clamp-3">
                  ${c.descripcion || '<em class="text-warmgray">Sin descripción detallada registrada.</em>'}
                </p>
              </div>

              <div class="mt-5 pt-3 border-t border-parchment-300 flex items-center justify-between gap-2">
                <button onclick="window.categoriasViewInstance.filtrarLibrosPorCategoria(${c.id})" class="text-xs font-semibold text-forest hover:text-gold flex items-center gap-1 font-display uppercase tracking-wider">
                  <i class="fa-solid fa-book-open text-[10px]"></i> Ver Libros
                </button>

                <div class="flex items-center gap-1">
                  ${isStaff ? `
                    <button onclick="window.categoriasViewInstance.abrirModalEditar(${c.id})" title="Editar Categoría" class="w-7 h-7 rounded-lg text-warmgray hover:text-forest hover:bg-parchment flex items-center justify-center transition text-xs">
                      <i class="fa-solid fa-pen-to-square"></i>
                    </button>
                  ` : ''}

                  ${isAdmin ? `
                    <button onclick="window.categoriasViewInstance.eliminarCategoria(${c.id}, '${c.nombre.replace(/'/g, "\\'")}')" title="Eliminar Categoría" class="w-7 h-7 rounded-lg text-warmgray hover:text-red-700 hover:bg-red-50 flex items-center justify-center transition text-xs">
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
        'window.categoriasViewInstance.cambiarPagina'
      );
    } catch (e) {
      listContainer.innerHTML = UI.emptyState('Error cargando categorías', e.message);
    }
  },

  cambiarPagina(nuevoSkip) {
    this.skip = nuevoSkip;
    this.cargarCategorias();
    window.scrollTo({ top: 200, behavior: 'smooth' });
  },

  filtrarLibrosPorCategoria(catId) {
    window.appRouter.navigate('libros', { categoria_id: catId });
  },

  abrirModalCrear() {
    const modalHtml = `
      <div id="modal-categoria-form" class="fixed inset-0 z-50 flex items-center justify-center p-4 modal-backdrop">
        <div class="bg-ivory rounded-3xl max-w-md w-full p-6 sm:p-8 shadow-2xl border border-parchment-300 modal-content-panel">
          <div class="flex items-center justify-between pb-3 border-b border-parchment-300">
            <div>
              <span class="text-[10px] font-display uppercase tracking-widest text-gold font-bold">Clasificación</span>
              <h3 class="font-editorial text-xl font-bold text-forest">Nueva Categoría</h3>
            </div>
            <button onclick="window.categoriasViewInstance.cerrarModalForm()" class="text-warmgray hover:text-forest text-xl">&times;</button>
          </div>

          <form onsubmit="window.categoriasViewInstance.guardarNuevaCategoria(event)" class="mt-4 space-y-4">
            <div>
              <label class="block text-xs font-bold text-forest mb-1">Nombre (3 a 50 letras) *</label>
              <input type="text" id="crear-categoria-nombre" required placeholder="Ej: realismo magico" class="w-full px-3 py-2 bg-parchment-50 border border-parchment-300 rounded-xl text-xs text-forest focus:ring-2 focus:ring-forest focus:outline-none">
            </div>

            <div>
              <label class="block text-xs font-bold text-forest mb-1">Descripción</label>
              <textarea id="crear-categoria-descripcion" rows="3" placeholder="Define las características del género o temática..." class="w-full px-3 py-2 bg-parchment-50 border border-parchment-300 rounded-xl text-xs text-forest focus:ring-2 focus:ring-forest focus:outline-none"></textarea>
            </div>

            <div class="pt-4 border-t border-parchment-300 flex justify-end gap-2">
              <button type="button" onclick="window.categoriasViewInstance.cerrarModalForm()" class="px-4 py-2 border border-parchment-300 rounded-xl text-xs font-semibold hover:bg-parchment">Cancelar</button>
              <button type="submit" class="px-5 py-2 bg-forest text-parchment-50 font-bold rounded-xl text-xs shadow-md">Guardar</button>
            </div>
          </form>
        </div>
      </div>
    `;

    document.getElementById('modal-portal').innerHTML = modalHtml;
  },

  async guardarNuevaCategoria(e) {
    e.preventDefault();
    const payload = {
      nombre: document.getElementById('crear-categoria-nombre').value.trim().toLowerCase(),
      descripcion: document.getElementById('crear-categoria-descripcion').value.trim() || null
    };

    try {
      await categoriasService.crear(payload);
      this.cerrarModalForm();
      UI.toast('Categoría agregada');
      this.cargarCategorias();
    } catch (err) {
      UI.toast(err.message, 'error');
    }
  },

  abrirModalEditar(id) {
    const cat = this.categorias.find(c => c.id === id);
    if (!cat) return;

    const modalHtml = `
      <div id="modal-categoria-form" class="fixed inset-0 z-50 flex items-center justify-center p-4 modal-backdrop">
        <div class="bg-ivory rounded-3xl max-w-md w-full p-6 sm:p-8 shadow-2xl border border-parchment-300 modal-content-panel">
          <div class="flex items-center justify-between pb-3 border-b border-parchment-300">
            <div>
              <span class="text-[10px] font-display uppercase tracking-widest text-gold font-bold">Edición</span>
              <h3 class="font-editorial text-xl font-bold text-forest">Editar Categoría</h3>
            </div>
            <button onclick="window.categoriasViewInstance.cerrarModalForm()" class="text-warmgray hover:text-forest text-xl">&times;</button>
          </div>

          <form onsubmit="window.categoriasViewInstance.guardarEdicionCategoria(event, ${cat.id})" class="mt-4 space-y-4">
            <div>
              <label class="block text-xs font-bold text-forest mb-1">Nombre *</label>
              <input type="text" id="editar-categoria-nombre" required value="${cat.nombre}" class="w-full px-3 py-2 bg-parchment-50 border border-parchment-300 rounded-xl text-xs text-forest focus:ring-2 focus:ring-forest focus:outline-none">
            </div>

            <div>
              <label class="block text-xs font-bold text-forest mb-1">Descripción</label>
              <textarea id="editar-categoria-descripcion" rows="3" class="w-full px-3 py-2 bg-parchment-50 border border-parchment-300 rounded-xl text-xs text-forest focus:ring-2 focus:ring-forest focus:outline-none">${cat.descripcion || ''}</textarea>
            </div>

            <div class="pt-4 border-t border-parchment-300 flex justify-end gap-2">
              <button type="button" onclick="window.categoriasViewInstance.cerrarModalForm()" class="px-4 py-2 border border-parchment-300 rounded-xl text-xs font-semibold hover:bg-parchment">Cancelar</button>
              <button type="submit" class="px-5 py-2 bg-forest text-parchment-50 font-bold rounded-xl text-xs shadow-md">Actualizar</button>
            </div>
          </form>
        </div>
      </div>
    `;

    document.getElementById('modal-portal').innerHTML = modalHtml;
  },

  async guardarEdicionCategoria(e, id) {
    e.preventDefault();
    const payload = {
      nombre: document.getElementById('editar-categoria-nombre').value.trim().toLowerCase(),
      descripcion: document.getElementById('editar-categoria-descripcion').value.trim() || null
    };

    try {
      await categoriasService.actualizar(id, payload);
      this.cerrarModalForm();
      UI.toast('Categoría actualizada');
      this.cargarCategorias();
    } catch (err) {
      UI.toast(err.message, 'error');
    }
  },

  cerrarModalForm() {
    document.getElementById('modal-portal').innerHTML = '';
  },

  async eliminarCategoria(id, nombre) {
    const ok = await UI.confirm('¿Eliminar categoría?', `¿Deseas dar de baja "${nombre}"?`, 'Eliminar', true);
    if (!ok) return;

    try {
      await categoriasService.eliminar(id);
      UI.toast('Categoría eliminada');
      this.cargarCategorias();
    } catch (err) {
      UI.toast(err.message, 'error');
    }
  }
};
