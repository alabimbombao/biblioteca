/**
 * VISTA: INICIO / DASHBOARD
 * Presenta el resumen visual de la biblioteca con datos 100% reales.
 */

import { reportesService } from '../../services/reportesService.js';
import { librosService } from '../../services/librosService.js';
import { store } from '../../state.js';
import { UI } from '../components.js';

export const dashboardView = {
  async render(container) {
    container.innerHTML = UI.loadingSpinner('Consultando registros de la biblioteca...');

    const { currentUser, isStaff } = store.get();

    try {
      let stats = {
        total_libros: 0,
        total_ejemplares: 0,
        total_prestados: 0,
        total_socios_activos: 0,
        total_socios_vencidos: 0,
        total_multas: 0
      };

      let librosDestacados = [];

      // Si es Staff (Admin o Bibliotecario), consultar el endpoint real de reportes
      if (isStaff) {
        try {
          stats = await reportesService.resumen();
        } catch (e) {
          console.warn('No se pudo cargar el resumen de reportes:', e);
        }

        try {
          librosDestacados = await reportesService.librosMasPrestados(4);
        } catch (e) {
          console.warn('No se pudieron cargar los libros más prestados:', e);
        }
      } else {
        // Para visitantes / socios, agregar stats desde el catálogo público
        try {
          // Traer todos los libros para calcular totales reales (máx 100 según el backend)
          const resAllLibros = await librosService.listar({ limit: 100 });
          const todosLosLibros = resAllLibros.items || [];
          stats.total_libros = resAllLibros.total || 0;

          let totalEjemplares = 0;
          let totalDisponibles = 0;
          todosLosLibros.forEach(l => {
            totalEjemplares += (l.ejemplares || 0);
            totalDisponibles += (l.disponibles || 0);
          });
          stats.total_ejemplares = totalEjemplares;
          stats.total_prestados = totalEjemplares - totalDisponibles;

          // Libros destacados: primeros 4 ordenados por mayor circulación (ejemplares - disponibles)
          librosDestacados = [...todosLosLibros]
            .sort((a, b) => (b.ejemplares - b.disponibles) - (a.ejemplares - a.disponibles))
            .slice(0, 4)
            .map(l => ({
              libro_id: l.id,
              titulo: l.titulo,
              autor: l.autor ? l.autor.nombre : 'Sin autor',
              total_prestamos: l.ejemplares - l.disponibles
            }));
        } catch (e) {
          console.warn('Error cargando libros públicos:', e);
        }
      }

      const bienvenida = currentUser 
        ? `Bienvenido, <span class="text-gold italic font-editorial">${currentUser.email.split('@')[0]}</span>`
        : `Bienvenido a la <span class="text-gold font-editorial">Biblioteca Digital</span>`;

      container.innerHTML = `
        <div class="space-y-8 animate-fade-in">
          
          <!-- BANNER EDITORIAL DE BIENVENIDA -->
          <div class="relative overflow-hidden rounded-3xl bg-gradient-to-r from-forest to-forest-dark text-parchment-50 p-8 sm:p-10 shadow-xl border border-parchment-300/20">
            <div class="absolute -right-8 -bottom-8 opacity-10 pointer-events-none text-parchment-50 text-9xl">
              <i class="fa-solid fa-book-open-reader"></i>
            </div>
            
            <div class="relative z-10 max-w-2xl">
              <span class="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-display tracking-widest uppercase bg-gold/20 text-gold-light border border-gold/40 mb-3">
                <i class="fa-solid fa-landmark"></i> Archivo & Catálogo
              </span>
              <h2 class="text-3xl sm:text-4xl font-bold font-editorial leading-tight tracking-tight">${bienvenida}</h2>
              <p class="mt-3 text-xs sm:text-sm text-parchment-200/90 leading-relaxed font-sans">
                Sistema centralizado de consulta bibliográfica, preservación y circulación literaria. Gestiona ejemplares, autores, socios y préstamos respetando las normativas de la biblioteca.
              </p>

              <div class="mt-6 flex flex-wrap gap-3">
                <button onclick="window.appRouter.navigate('libros')" class="bg-gold hover:bg-gold-light text-forest-dark font-display uppercase tracking-wider px-5 py-2.5 rounded-xl text-xs font-bold shadow-md transition flex items-center gap-2">
                  <i class="fa-solid fa-magnifying-glass"></i> Explorar Catálogo
                </button>
                ${isStaff ? `
                  <button onclick="window.appRouter.navigate('prestamos')" class="bg-forest-light hover:bg-forest text-parchment-50 border border-parchment-300/40 font-display uppercase tracking-wider px-5 py-2.5 rounded-xl text-xs font-bold transition flex items-center gap-2">
                    <i class="fa-solid fa-hand-holding-hand text-gold"></i> Préstamos
                  </button>
                ` : ''}
              </div>
            </div>
          </div>

          <!-- MÉTRICAS EN TIEMPO REAL (DATOS REALES DEL BACKEND) -->
          <div>
            <div class="flex items-center justify-between mb-4">
              <h3 class="font-editorial text-xl font-bold text-forest">Estado del Archivo</h3>
              <span class="text-xs text-warmgray font-display tracking-wider uppercase">Registros Válidos</span>
            </div>

            <div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
              
              <div class="bg-parchment-50 p-4 rounded-2xl border border-parchment-300 shadow-sm flex flex-col justify-between">
                <div class="w-8 h-8 rounded-lg bg-parchment-200 text-forest flex items-center justify-center text-sm mb-2">
                  <i class="fa-solid fa-book"></i>
                </div>
                <span class="text-[11px] font-bold uppercase tracking-wider text-warmgray">Títulos</span>
                <span class="text-2xl font-bold font-editorial text-forest mt-1">${stats.total_libros}</span>
              </div>

              <div class="bg-parchment-50 p-4 rounded-2xl border border-parchment-300 shadow-sm flex flex-col justify-between">
                <div class="w-8 h-8 rounded-lg bg-parchment-200 text-forest flex items-center justify-center text-sm mb-2">
                  <i class="fa-solid fa-layer-group"></i>
                </div>
                <span class="text-[11px] font-bold uppercase tracking-wider text-warmgray">Ejemplares</span>
                <span class="text-2xl font-bold font-editorial text-forest mt-1">${stats.total_ejemplares || '—'}</span>
              </div>

              <div class="bg-parchment-50 p-4 rounded-2xl border border-parchment-300 shadow-sm flex flex-col justify-between">
                <div class="w-8 h-8 rounded-lg bg-parchment-200 text-forest flex items-center justify-center text-sm mb-2">
                  <i class="fa-solid fa-arrow-right-arrow-left"></i>
                </div>
                <span class="text-[11px] font-bold uppercase tracking-wider text-warmgray">En Préstamo</span>
                <span class="text-2xl font-bold font-editorial text-olive mt-1">${stats.total_prestados || '—'}</span>
              </div>

              <div class="bg-parchment-50 p-4 rounded-2xl border border-parchment-300 shadow-sm flex flex-col justify-between" title="${!isStaff ? 'Requiere autenticación de personal' : ''}">
                <div class="w-8 h-8 rounded-lg bg-parchment-200 text-forest flex items-center justify-center text-sm mb-2">
                  <i class="fa-solid fa-users"></i>
                </div>
                <span class="text-[11px] font-bold uppercase tracking-wider text-warmgray">Socios Activos</span>
                <span class="text-2xl font-bold font-editorial text-forest mt-1">
                  ${isStaff ? stats.total_socios_activos : '<span class="text-warmgray text-lg" title="Solo visible para personal">—</span>'}
                </span>
              </div>

              <div class="bg-parchment-50 p-4 rounded-2xl border border-parchment-300 shadow-sm flex flex-col justify-between" title="${!isStaff ? 'Requiere autenticación de personal' : ''}">
                <div class="w-8 h-8 rounded-lg bg-parchment-200 text-forest flex items-center justify-center text-sm mb-2">
                  <i class="fa-solid fa-clock text-amber-700"></i>
                </div>
                <span class="text-[11px] font-bold uppercase tracking-wider text-warmgray">Vencidos</span>
                <span class="text-2xl font-bold font-editorial text-amber-800 mt-1">
                  ${isStaff ? (stats.total_socios_vencidos || '0') : '<span class="text-warmgray text-lg" title="Solo visible para personal">—</span>'}
                </span>
              </div>

              <div class="bg-parchment-50 p-4 rounded-2xl border border-parchment-300 shadow-sm flex flex-col justify-between" title="${!isStaff ? 'Requiere autenticación de personal' : ''}">
                <div class="w-8 h-8 rounded-lg bg-parchment-200 text-forest flex items-center justify-center text-sm mb-2">
                  <i class="fa-solid fa-coins text-gold"></i>
                </div>
                <span class="text-[11px] font-bold uppercase tracking-wider text-warmgray">Multas Total</span>
                <span class="text-2xl font-bold font-editorial text-forest mt-1">
                  ${isStaff ? '$' + parseFloat(stats.total_multas || 0).toFixed(2) : '<span class="text-warmgray text-lg" title="Solo visible para personal">—</span>'}
                </span>
              </div>

            </div>
          </div>

          <!-- SECCIÓN EDITORIAL: OBRAS DESTACADAS / MÁS SOLICITADAS -->
          <div class="bg-parchment-light p-6 sm:p-8 rounded-3xl border border-parchment-300 shadow-sm">
            <div class="flex items-center justify-between mb-6 pb-4 border-b border-parchment-300">
              <div>
                <h3 class="font-editorial text-xl font-bold text-forest">
                  ${isStaff ? 'Obras de Mayor Circulación' : 'Novedades Literarias'}
                </h3>
                <p class="text-xs text-warmgray mt-0.5">Títulos con mayor demanda en el acervo bibliográfico</p>
              </div>
              <button onclick="window.appRouter.navigate('libros')" class="text-xs font-semibold text-forest hover:text-gold transition flex items-center gap-1 font-display uppercase tracking-wider">
                Ver todos <i class="fa-solid fa-arrow-right text-[10px]"></i>
              </button>
            </div>

            <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              ${librosDestacados.length > 0 ? librosDestacados.map(item => `
                <div class="bg-ivory p-4 rounded-2xl border border-parchment-300 shadow-sm flex flex-col justify-between book-spine-card">
                  <div>
                    <div class="h-28 bg-forest rounded-xl mb-3 flex items-center justify-center text-parchment-200 text-center p-3 relative overflow-hidden">
                      <div class="absolute inset-0 bg-parchment-pattern opacity-10"></div>
                      <i class="fa-solid fa-book-bookmark text-3xl text-gold/40 absolute -bottom-2 -right-2"></i>
                      <p class="font-editorial text-sm font-bold text-parchment-50 line-clamp-2">${item.titulo}</p>
                    </div>
                    <h4 class="font-editorial text-sm font-bold text-forest line-clamp-1" title="${item.titulo}">${item.titulo}</h4>
                    <p class="text-xs text-warmgray-dark flex items-center gap-1.5 mt-1 font-sans">
                      <i class="fa-solid fa-feather-pointed text-gold text-[10px]"></i> ${item.autor}
                    </p>
                  </div>
                  <div class="mt-4 pt-2 border-t border-parchment-300 flex items-center justify-between text-[11px] text-warmgray">
                    <span>${isStaff ? 'Préstamos acumulados:' : 'Disponibilidad activa'}</span>
                    <span class="font-bold text-forest">${item.total_prestamos}</span>
                  </div>
                </div>
              `).join('') : `
                <div class="col-span-full py-8 text-center text-xs text-warmgray">No se han registrado movimientos recientes aún.</div>
              `}
            </div>
          </div>

        </div>
      `;
    } catch (error) {
      container.innerHTML = UI.emptyState('Error de conexión', error.message);
    }
  }
};
