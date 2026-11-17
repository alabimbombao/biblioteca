/**
 * VISTA: CATÁLOGO DE LIBROS
 * Gestión integral de libros: búsqueda, filtrado, paginación, portadas y CRUD completo.
 */

import { librosService } from '../../services/librosService.js';
import { autoresService } from '../../services/autoresService.js';
import { categoriasService } from '../../services/categoriasService.js';
import { store } from '../../state.js';
import { UI } from '../components.js';

export const librosView = {
  skip: 0,
  limit: 12,
  filtros: {
    buscar: '',
    autor: '',
    categoria_id: '',
    desde: '',
    hasta: '',
    orden: 'titulo'
  },
  librosActuales: [],

  async render(container) {
    const { isStaff, isAdmin } = store.get();

    container.innerHTML = `
      <div class="space-y-6 animate-fade-in">

        <!-- CABECERA DE SECCIÓN EDITORIAL -->
        <div class="flex flex-col md:flex-row md:items-center md:justify-between gap-4 pb-4 border-b border-parchment-300">
          <div>
            <div class="flex items-center gap-2">
              <span class="text-xs font-display tracking-widest uppercase text-gold font-bold">Acervo Bibliográfico</span>
            </div>
            <h2 class="text-2xl sm:text-3xl font-bold font-editorial text-forest">Catálogo de Libros</h2>
            <p class="text-xs text-warmgray mt-1">Explora las obras disponibles, filtra por género, época o autoría.</p>
          </div>

          ${isStaff ? `
            <button onclick="window.librosViewInstance.abrirModalCrear()" class="inline-flex items-center gap-2 bg-forest hover:bg-forest-light text-parchment-50 font-display uppercase tracking-wider text-xs font-bold px-4 py-2.5 rounded-xl shadow-md transition self-start md:self-auto">
              <i class="fa-solid fa-plus text-gold"></i> Registrar Nuevo Libro
            </button>
          ` : ''}
        </div>

        <!-- PANEL DE BÚSQUEDA Y FILTRADO AVANZADO -->
        <div class="bg-parchment-50 p-4 sm:p-5 rounded-3xl border border-parchment-300 shadow-sm space-y-3">
          <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
            
            <!-- Búsqueda por título -->
            <div class="relative">
              <span class="absolute inset-y-0 left-0 pl-3.5 flex items-center text-warmgray pointer-events-none">
                <i class="fa-solid fa-magnifying-glass text-xs"></i>
              </span>
              <input type="text" id="filtro-buscar" placeholder="Buscar por título..." 
                     value="${this.filtros.buscar}"
                     class="w-full pl-9 pr-3 py-2 bg-ivory border border-parchment-300 rounded-xl text-xs text-forest focus:ring-2 focus:ring-forest focus:outline-none">
            </div>

            <!-- Filtro por Autor -->
            <div class="relative">
              <select id="filtro-autor" class="w-full px-3 py-2 bg-ivory border border-parchment-300 rounded-xl text-xs text-forest focus:ring-2 focus:ring-forest focus:outline-none">
                <option value="">Todos los Autores</option>
              </select>
            </div>

            <!-- Filtro por Categoría -->
            <div class="relative">
              <select id="filtro-categoria" class="w-full px-3 py-2 bg-ivory border border-parchment-300 rounded-xl text-xs text-forest focus:ring-2 focus:ring-forest focus:outline-none">
                <option value="">Todas las Categorías</option>
              </select>
            </div>

            <!-- Criterio de Ordenamiento -->
            <div class="relative">
              <select id="filtro-orden" class="w-full px-3 py-2 bg-ivory border border-parchment-300 rounded-xl text-xs text-forest focus:ring-2 focus:ring-forest focus:outline-none">
                <option value="titulo" ${this.filtros.orden === 'titulo' ? 'selected' : ''}>Ordenar: Título (A-Z)</option>
                <option value="anio" ${this.filtros.orden === 'anio' ? 'selected' : ''}>Ordenar: Año de Publicación</option>
              </select>
            </div>

          </div>

          <div class="flex flex-wrap items-center justify-between gap-3 pt-2 text-xs text-warmgray">
            <div class="flex items-center gap-2">
              <span>Año de publicación:</span>
              <input type="number" id="filtro-desde" placeholder="Desde (1450)" value="${this.filtros.desde}" class="w-24 px-2 py-1 bg-ivory border border-parchment-300 rounded-lg text-xs text-forest">
              <span>hasta</span>
              <input type="number" id="filtro-hasta" placeholder="Año actual" value="${this.filtros.hasta}" class="w-24 px-2 py-1 bg-ivory border border-parchment-300 rounded-lg text-xs text-forest">
            </div>

            <div class="flex items-center gap-2">
              <button onclick="window.librosViewInstance.aplicarFiltros()" class="px-3.5 py-1.5 bg-forest hover:bg-forest-light text-parchment-50 rounded-xl font-semibold shadow-sm transition text-xs">
                Filtrar Catálogo
              </button>
              <button onclick="window.librosViewInstance.limpiarFiltros()" class="px-3 py-1.5 bg-parchment-100 hover:bg-parchment-200 text-warmgray-dark rounded-xl font-medium transition text-xs">
                Restablecer
              </button>
            </div>
          </div>
        </div>

        <!-- CONTENEDOR DE LIBROS (GRID) -->
        <div id="libros-lista-container">
          ${UI.loadingSpinner('Recuperando volúmenes del catálogo...')}
        </div>

        <!-- PAGINACIÓN -->
        <div id="libros-paginacion-container"></div>

      </div>
    `;

    window.librosViewInstance = this;
    await this.cargarCatalogosAuxiliares();
    await this.cargarLibros();
  },

  async cargarCatalogosAuxiliares() {
    try {
      const [resAutores, resCategorias] = await Promise.all([
        autoresService.listar({ limit: 100 }),
        categoriasService.listar({ limit: 100 })
      ]);

      const autores = resAutores.items || [];
      const categorias = resCategorias.items || [];

      store.setAutores(autores);
      store.setCategorias(categorias);

      const selAutor = document.getElementById('filtro-autor');
      if (selAutor) {
        selAutor.innerHTML = '<option value="">Todos los Autores</option>' + 
          autores.map(a => `<option value="${a.nombre}">${a.nombre}</option>`).join('');
        if (this.filtros.autor) selAutor.value = this.filtros.autor;
      }

      const selCat = document.getElementById('filtro-categoria');
      if (selCat) {
        selCat.innerHTML = '<option value="">Todas las Categorías</option>' + 
          categorias.map(c => `<option value="${c.id}">${c.nombre}</option>`).join('');
        if (this.filtros.categoria_id) selCat.value = this.filtros.categoria_id;
      }
    } catch (e) {
      console.warn('Error cargando catálogos auxiliares:', e);
    }
  },

  async cargarLibros() {
    const listContainer = document.getElementById('libros-lista-container');
    const pagContainer = document.getElementById('libros-paginacion-container');
    if (!listContainer) return;

    listContainer.innerHTML = UI.loadingSpinner('Cargando estanterías...');

    try {
      const params = {
        skip: this.skip,
        limit: this.limit,
        buscar: this.filtros.buscar || null,
        autor: this.filtros.autor || null,
        categoria_id: this.filtros.categoria_id ? parseInt(this.filtros.categoria_id) : null,
        desde: this.filtros.desde ? parseInt(this.filtros.desde) : null,
        hasta: this.filtros.hasta ? parseInt(this.filtros.hasta) : null,
        orden: this.filtros.orden || 'titulo'
      };

      const res = await librosService.listar(params);
      const libros = res.items || [];
      this.librosActuales = libros;

      if (libros.length === 0) {
        listContainer.innerHTML = UI.emptyState(
          'Ninguna obra coincide con los criterios',
          'Verifica los filtros aplicados o busca por otro término en el catálogo.',
          store.get().isStaff ? 'Registrar Libro' : null,
          'window.librosViewInstance.abrirModalCrear()'
        );
        pagContainer.innerHTML = '';
        return;
      }

      const { isStaff, isAdmin } = store.get();

      listContainer.innerHTML = `
        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
          ${libros.map(libro => this.renderTarjetaLibro(libro, isStaff, isAdmin)).join('')}
        </div>
      `;

      pagContainer.innerHTML = UI.renderPagination(
        res.total,
        this.skip,
        this.limit,
        'window.librosViewInstance.cambiarPagina'
      );
    } catch (err) {
      listContainer.innerHTML = UI.emptyState('Error al cargar libros', err.message);
    }
  },

  renderTarjetaLibro(l, isStaff, isAdmin) {
    const portadaHtml = l.portada_url
      ? `<img src="${l.portada_url}" alt="${l.titulo}" class="w-full h-52 object-cover rounded-2xl shadow-inner transition duration-300 hover:scale-[1.02]">`
      : `<div class="w-full h-52 rounded-2xl bg-gradient-to-br from-forest-dark via-forest to-walnut-dark p-5 flex flex-col justify-between text-parchment-50 relative overflow-hidden shadow-inner">
           <div class="absolute -right-4 -bottom-4 text-parchment-50/10 text-8xl font-display pointer-events-none">
             <i class="fa-solid fa-book-bookmark"></i>
           </div>
           <div class="flex justify-between items-start">
             <span class="text-[10px] font-display uppercase tracking-widest text-gold-light bg-forest-dark/60 px-2 py-0.5 rounded-md border border-gold/30">Ex Libris</span>
             <i class="fa-solid fa-feather-pointed text-gold text-xs"></i>
           </div>
           <div>
             <h4 class="font-editorial text-base font-bold leading-snug line-clamp-2 text-parchment-100">${l.titulo}</h4>
             <p class="text-xs text-parchment-300 font-sans mt-1 line-clamp-1">${l.autor ? l.autor.nombre : 'Autor anónimo'}</p>
           </div>
           <div class="text-[10px] text-parchment-400 font-mono tracking-wider pt-2 border-t border-parchment-300/20">
             ISBN ${l.isbn}
           </div>
         </div>`;

    const dispBadge = l.disponibles > 0 
      ? `<span class="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-emerald-50 text-emerald-800 border border-emerald-200">
           <span class="w-1.5 h-1.5 rounded-full bg-emerald-500"></span> ${l.disponibles} de ${l.ejemplares} Disp.
         </span>`
      : `<span class="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-red-50 text-red-800 border border-red-200">
           <span class="w-1.5 h-1.5 rounded-full bg-red-500"></span> Agotado (${l.ejemplares} prestados)
         </span>`;

    const catBadges = (l.categorias || []).map(c => 
      `<span class="inline-block px-2 py-0.5 rounded-md text-[10px] font-medium bg-parchment text-forest-dark border border-parchment-300 capitalize">${c.nombre}</span>`
    ).join(' ');

    return `
      <div class="bg-parchment-light rounded-3xl border border-parchment-300 p-4 shadow-sm hover:shadow-md transition flex flex-col justify-between book-spine-card">
        <div>
          <!-- Portada -->
          <div class="relative mb-3.5">
            ${portadaHtml}
            <div class="absolute top-2.5 right-2.5">
              ${dispBadge}
            </div>
          </div>

          <!-- Metadatos de la Obra -->
          <div class="space-y-1">
            <h3 class="font-editorial text-base font-bold text-forest leading-snug line-clamp-1 hover:line-clamp-none transition" title="${l.titulo}">
              ${l.titulo}
            </h3>
            
            <p class="text-xs font-semibold text-walnut flex items-center gap-1.5 font-sans">
              <i class="fa-solid fa-feather-pointed text-gold text-[11px]"></i>
              <span>${l.autor ? l.autor.nombre : 'Sin autor'}</span>
            </p>

            <div class="flex items-center gap-2 text-[11px] text-warmgray pt-0.5 font-sans">
              <span>Año: <strong class="text-forest font-semibold">${l.anio_publicacion}</strong></span>
              <span>•</span>
              <span class="font-mono text-[10px]">ISBN: ${l.isbn}</span>
            </div>

            <!-- Etiquetas de Categorías -->
            <div class="flex flex-wrap gap-1 pt-2">
              ${catBadges}
            </div>
          </div>
        </div>

        <!-- Acciones Inferiores -->
        <div class="mt-4 pt-3 border-t border-parchment-300 flex items-center justify-between gap-2">
          ${isStaff ? `
            <button onclick="window.librosViewInstance.abrirModalPrestar(${l.id})" 
                    ${l.disponibles <= 0 ? 'disabled' : ''} 
                    class="text-xs font-semibold px-3 py-1.5 rounded-xl transition flex items-center gap-1.5 ${l.disponibles > 0 ? 'bg-forest hover:bg-forest-light text-parchment-50 shadow-sm' : 'bg-parchment-200 text-warmgray cursor-not-allowed'}">
              <i class="fa-solid fa-hand-holding-hand text-gold text-[10px]"></i> Prestar
            </button>
          ` : `
            <span class="text-[11px] text-warmgray italic">Consulta en sala</span>
          `}

          <div class="flex items-center gap-1">
            ${isStaff ? `
              <button onclick="window.librosViewInstance.abrirModalPortada(${l.id})" title="Gestionar Portada" class="w-7 h-7 rounded-lg text-warmgray hover:text-forest hover:bg-parchment flex items-center justify-center transition text-xs">
                <i class="fa-solid fa-image"></i>
              </button>
              <button onclick="window.librosViewInstance.abrirModalEditar(${l.id})" title="Editar Libro" class="w-7 h-7 rounded-lg text-warmgray hover:text-forest hover:bg-parchment flex items-center justify-center transition text-xs">
                <i class="fa-solid fa-pen-to-square"></i>
              </button>
            ` : ''}

            ${isAdmin ? `
              <button onclick="window.librosViewInstance.eliminarLibro(${l.id}, '${l.titulo.replace(/'/g, "\\'")}')" title="Eliminar Libro" class="w-7 h-7 rounded-lg text-warmgray hover:text-red-700 hover:bg-red-50 flex items-center justify-center transition text-xs">
                <i class="fa-solid fa-trash-can"></i>
              </button>
            ` : ''}
          </div>
        </div>
      </div>
    `;
  },

  aplicarFiltros() {
    this.filtros.buscar = document.getElementById('filtro-buscar').value.trim();
    this.filtros.autor = document.getElementById('filtro-autor').value;
    this.filtros.categoria_id = document.getElementById('filtro-categoria').value;
    this.filtros.desde = document.getElementById('filtro-desde').value;
    this.filtros.hasta = document.getElementById('filtro-hasta').value;
    this.filtros.orden = document.getElementById('filtro-orden').value;
    this.skip = 0;
    this.cargarLibros();
  },

  limpiarFiltros() {
    this.filtros = {
      buscar: '',
      autor: '',
      categoria_id: '',
      desde: '',
      hasta: '',
      orden: 'titulo'
    };
    this.skip = 0;
    document.getElementById('filtro-buscar').value = '';
    document.getElementById('filtro-autor').value = '';
    document.getElementById('filtro-categoria').value = '';
    document.getElementById('filtro-desde').value = '';
    document.getElementById('filtro-hasta').value = '';
    document.getElementById('filtro-orden').value = 'titulo';
    this.cargarLibros();
  },

  cambiarPagina(nuevoSkip) {
    this.skip = nuevoSkip;
    this.cargarLibros();
    window.scrollTo({ top: 200, behavior: 'smooth' });
  },

  // Modal: Crear Libro
  abrirModalCrear() {
    const { autores, categorias } = store.get();
    const modalHtml = `
      <div id="modal-libro-form" class="fixed inset-0 z-50 flex items-center justify-center p-4 modal-backdrop">
        <div class="bg-ivory rounded-3xl max-w-lg w-full p-6 sm:p-8 shadow-2xl border border-parchment-300 max-h-[90vh] overflow-y-auto modal-content-panel">
          <div class="flex items-center justify-between pb-4 border-b border-parchment-300">
            <div>
              <span class="text-[10px] font-display uppercase tracking-widest text-gold font-bold">Catálogo</span>
              <h3 class="font-editorial text-xl font-bold text-forest">Registrar Nuevo Libro</h3>
            </div>
            <button onclick="window.librosViewInstance.cerrarModalForm()" class="text-warmgray hover:text-forest text-xl">&times;</button>
          </div>

          <form id="form-libro-guardar" onsubmit="window.librosViewInstance.guardarNuevoLibro(event)" class="mt-5 space-y-4">
            <div>
              <label class="block text-xs font-bold text-forest mb-1">Título de la Obra *</label>
              <input type="text" id="crear-libro-titulo" required placeholder="Ej: Cien Años de Soledad" class="w-full px-3 py-2 bg-parchment-50 border border-parchment-300 rounded-xl text-xs text-forest focus:ring-2 focus:ring-forest focus:outline-none">
            </div>

            <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div>
                <label class="block text-xs font-bold text-forest mb-1">ISBN (13 dígitos) *</label>
                <input type="text" id="crear-libro-isbn" required maxlength="13" placeholder="9788437604947" class="w-full px-3 py-2 bg-parchment-50 border border-parchment-300 rounded-xl text-xs text-forest focus:ring-2 focus:ring-forest focus:outline-none">
              </div>
              <div>
                <label class="block text-xs font-bold text-forest mb-1">Año de Publicación *</label>
                <input type="number" id="crear-libro-anio" required min="1450" max="${new Date().getFullYear()}" placeholder="1967" class="w-full px-3 py-2 bg-parchment-50 border border-parchment-300 rounded-xl text-xs text-forest focus:ring-2 focus:ring-forest focus:outline-none">
              </div>
            </div>

            <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div>
                <label class="block text-xs font-bold text-forest mb-1">Total Ejemplares Físicos (1-50) *</label>
                <input type="number" id="crear-libro-ejemplares" required min="1" max="50" value="3" class="w-full px-3 py-2 bg-parchment-50 border border-parchment-300 rounded-xl text-xs text-forest focus:ring-2 focus:ring-forest focus:outline-none">
              </div>
              <div>
                <label class="block text-xs font-bold text-forest mb-1">Autor Responsable *</label>
                <select id="crear-libro-autor-id" required class="w-full px-3 py-2 bg-parchment-50 border border-parchment-300 rounded-xl text-xs text-forest focus:ring-2 focus:ring-forest focus:outline-none">
                  <option value="">-- Seleccionar Autor --</option>
                  ${autores.map(a => `<option value="${a.id}">${a.nombre} (${a.nacionalidad || 'N/A'})</option>`).join('')}
                </select>
              </div>
            </div>

            <div>
              <label class="block text-xs font-bold text-forest mb-1">Categorías Literarias (Selecciona de 1 a 5) *</label>
              <div class="grid grid-cols-2 gap-2 max-h-32 overflow-y-auto p-2.5 bg-parchment-50 border border-parchment-300 rounded-xl text-xs">
                ${categorias.map(c => `
                  <label class="flex items-center space-x-2 p-1 rounded hover:bg-parchment cursor-pointer">
                    <input type="checkbox" name="crear_libro_cat" value="${c.id}" class="rounded text-forest focus:ring-forest">
                    <span class="truncate capitalize">${c.nombre}</span>
                  </label>
                `).join('')}
              </div>
            </div>

            <div class="pt-4 border-t border-parchment-300 flex justify-end gap-2">
              <button type="button" onclick="window.librosViewInstance.cerrarModalForm()" class="px-4 py-2 border border-parchment-300 text-warmgray-dark rounded-xl text-xs font-semibold hover:bg-parchment transition">Cancelar</button>
              <button type="submit" class="px-5 py-2 bg-forest hover:bg-forest-light text-parchment-50 rounded-xl text-xs font-bold shadow-md transition">Guardar Obra</button>
            </div>
          </form>
        </div>
      </div>
    `;

    document.getElementById('modal-portal').innerHTML = modalHtml;
  },

  async guardarNuevoLibro(e) {
    e.preventDefault();
    const checkedCats = Array.from(document.querySelectorAll("input[name='crear_libro_cat']:checked")).map(c => parseInt(c.value));
    if (checkedCats.length === 0) {
      UI.toast('Debes elegir al menos una categoría', 'warning');
      return;
    }

    const payload = {
      titulo: document.getElementById('crear-libro-titulo').value.trim(),
      isbn: document.getElementById('crear-libro-isbn').value.trim(),
      anio_publicacion: parseInt(document.getElementById('crear-libro-anio').value),
      ejemplares: parseInt(document.getElementById('crear-libro-ejemplares').value),
      autor_id: parseInt(document.getElementById('crear-libro-autor-id').value),
      categoria_ids: checkedCats
    };

    try {
      await librosService.crear(payload);
      this.cerrarModalForm();
      UI.toast('Libro incorporado con éxito al acervo');
      this.cargarLibros();
    } catch (err) {
      UI.toast(err.message, 'error');
    }
  },

  // Modal: Editar Libro
  abrirModalEditar(id) {
    const libro = this.librosActuales.find(l => l.id === id);
    if (!libro) return;

    const { categorias } = store.get();
    const catIds = (libro.categorias || []).map(c => c.id);

    const modalHtml = `
      <div id="modal-libro-form" class="fixed inset-0 z-50 flex items-center justify-center p-4 modal-backdrop">
        <div class="bg-ivory rounded-3xl max-w-lg w-full p-6 sm:p-8 shadow-2xl border border-parchment-300 max-h-[90vh] overflow-y-auto modal-content-panel">
          <div class="flex items-center justify-between pb-4 border-b border-parchment-300">
            <div>
              <span class="text-[10px] font-display uppercase tracking-widest text-gold font-bold">Edición</span>
              <h3 class="font-editorial text-xl font-bold text-forest">Editar Obra</h3>
            </div>
            <button onclick="window.librosViewInstance.cerrarModalForm()" class="text-warmgray hover:text-forest text-xl">&times;</button>
          </div>

          <form id="form-libro-editar" onsubmit="window.librosViewInstance.guardarEdicionLibro(event, ${libro.id})" class="mt-5 space-y-4">
            <div>
              <label class="block text-xs font-bold text-forest mb-1">Título de la Obra *</label>
              <input type="text" id="editar-libro-titulo" required value="${libro.titulo}" class="w-full px-3 py-2 bg-parchment-50 border border-parchment-300 rounded-xl text-xs text-forest focus:ring-2 focus:ring-forest focus:outline-none">
            </div>

            <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div>
                <label class="block text-xs font-bold text-forest mb-1">Año de Publicación</label>
                <input type="number" id="editar-libro-anio" min="1450" max="${new Date().getFullYear()}" value="${libro.anio_publicacion}" class="w-full px-3 py-2 bg-parchment-50 border border-parchment-300 rounded-xl text-xs text-forest focus:ring-2 focus:ring-forest focus:outline-none">
              </div>
              <div>
                <label class="block text-xs font-bold text-forest mb-1">Total Ejemplares (Mínimo préstamos activos)</label>
                <input type="number" id="editar-libro-ejemplares" min="1" max="50" value="${libro.ejemplares}" class="w-full px-3 py-2 bg-parchment-50 border border-parchment-300 rounded-xl text-xs text-forest focus:ring-2 focus:ring-forest focus:outline-none">
              </div>
            </div>

            <div>
              <label class="block text-xs font-bold text-forest mb-1">Categorías Asignadas</label>
              <div class="grid grid-cols-2 gap-2 max-h-32 overflow-y-auto p-2.5 bg-parchment-50 border border-parchment-300 rounded-xl text-xs">
                ${categorias.map(c => `
                  <label class="flex items-center space-x-2 p-1 rounded hover:bg-parchment cursor-pointer">
                    <input type="checkbox" name="editar_libro_cat" value="${c.id}" ${catIds.includes(c.id) ? 'checked' : ''} class="rounded text-forest focus:ring-forest">
                    <span class="truncate capitalize">${c.nombre}</span>
                  </label>
                `).join('')}
              </div>
            </div>

            <div class="pt-4 border-t border-parchment-300 flex justify-end gap-2">
              <button type="button" onclick="window.librosViewInstance.cerrarModalForm()" class="px-4 py-2 border border-parchment-300 text-warmgray-dark rounded-xl text-xs font-semibold hover:bg-parchment transition">Cancelar</button>
              <button type="submit" class="px-5 py-2 bg-forest hover:bg-forest-light text-parchment-50 rounded-xl text-xs font-bold shadow-md transition">Actualizar Registro</button>
            </div>
          </form>
        </div>
      </div>
    `;

    document.getElementById('modal-portal').innerHTML = modalHtml;
  },

  async guardarEdicionLibro(e, id) {
    e.preventDefault();
    const checkedCats = Array.from(document.querySelectorAll("input[name='editar_libro_cat']:checked")).map(c => parseInt(c.value));

    const payload = {
      titulo: document.getElementById('editar-libro-titulo').value.trim(),
      anio_publicacion: parseInt(document.getElementById('editar-libro-anio').value),
      ejemplares: parseInt(document.getElementById('editar-libro-ejemplares').value),
      categoria_ids: checkedCats.length > 0 ? checkedCats : undefined
    };

    try {
      await librosService.actualizar(id, payload);
      this.cerrarModalForm();
      UI.toast('Registro bibliográfico actualizado');
      this.cargarLibros();
    } catch (err) {
      UI.toast(err.message, 'error');
    }
  },

  cerrarModalForm() {
    document.getElementById('modal-portal').innerHTML = '';
  },

  // Modal: Gestionar Portada
  abrirModalPortada(id) {
    const libro = this.librosActuales.find(l => l.id === id);
    if (!libro) return;

    const modalHtml = `
      <div id="modal-portada" class="fixed inset-0 z-50 flex items-center justify-center p-4 modal-backdrop">
        <div class="bg-ivory rounded-3xl max-w-sm w-full p-6 shadow-2xl border border-parchment-300 modal-content-panel">
          <div class="flex items-center justify-between pb-3 border-b border-parchment-300">
            <h3 class="font-editorial text-lg font-bold text-forest">Portada de la Obra</h3>
            <button onclick="window.librosViewInstance.cerrarModalForm()" class="text-warmgray hover:text-forest text-xl">&times;</button>
          </div>

          <div class="mt-4 space-y-4 text-xs">
            <p class="text-warmgray">Sube o reemplaza la imagen de portada (JPG, PNG o WEBP, máx 5 MB) alojada en Cloudinary.</p>

            ${libro.portada_url ? `
              <div class="text-center">
                <img src="${libro.portada_url}" class="w-32 h-44 object-cover mx-auto rounded-xl shadow-md border border-parchment-300">
                <button onclick="window.librosViewInstance.eliminarPortada(${libro.id})" class="mt-2 text-red-700 hover:text-red-900 font-semibold text-xs flex items-center justify-center gap-1 mx-auto">
                  <i class="fa-solid fa-trash-can"></i> Quitar portada actual
                </button>
              </div>
            ` : ''}

            <input type="file" id="archivo-portada-input" accept="image/png, image/jpeg, image/webp" 
                   class="block w-full text-xs text-warmgray file:mr-3 file:py-2 file:px-4 file:rounded-xl file:border-0 file:text-xs file:font-semibold file:bg-forest file:text-parchment-50 hover:file:bg-forest-light cursor-pointer">

            <div class="pt-3 border-t border-parchment-300 flex justify-end gap-2">
              <button onclick="window.librosViewInstance.cerrarModalForm()" class="px-3 py-1.5 border border-parchment-300 rounded-xl font-semibold">Cerrar</button>
              <button onclick="window.librosViewInstance.subirArchivoPortada(${libro.id})" class="px-4 py-1.5 bg-forest text-parchment-50 font-bold rounded-xl shadow-sm">Subir Portada</button>
            </div>
          </div>
        </div>
      </div>
    `;

    document.getElementById('modal-portal').innerHTML = modalHtml;
  },

  async subirArchivoPortada(id) {
    const input = document.getElementById('archivo-portada-input');
    if (!input.files || input.files.length === 0) {
      UI.toast('Selecciona un archivo de imagen primero', 'warning');
      return;
    }

    try {
      await librosService.subirPortada(id, input.files[0]);
      this.cerrarModalForm();
      UI.toast('Portada actualizada correctamente');
      this.cargarLibros();
    } catch (err) {
      UI.toast(err.message, 'error');
    }
  },

  async eliminarPortada(id) {
    const ok = await UI.confirm('¿Quitar portada?', '¿Deseas desvincular la portada de este libro?');
    if (!ok) return;

    try {
      await librosService.eliminarPortada(id);
      this.cerrarModalForm();
      UI.toast('Portada removida');
      this.cargarLibros();
    } catch (err) {
      UI.toast(err.message, 'error');
    }
  },

  async eliminarLibro(id, titulo) {
    const ok = await UI.confirm(
      '¿Eliminar obra del archivo?',
      `¿Confirmas la baja permanente de "${titulo}"? Solo se permite si no cuenta con préstamos activos.`,
      'Sí, eliminar obra',
      true
    );
    if (!ok) return;

    try {
      await librosService.eliminar(id);
      UI.toast('Libro eliminado del catálogo');
      this.cargarLibros();
    } catch (err) {
      UI.toast(err.message, 'error');
    }
  },

  abrirModalPrestar(libroId) {
    window.appRouter.navigate('prestamos', { libroId });
  }
};
