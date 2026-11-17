/**
 * VISTA: REPORTES Y ESTADÍSTICAS
 * Solo accesible para el personal (Staff). Conecta con /api/v1/reportes.
 */

import { reportesService } from '../../services/reportesService.js';
import { store } from '../../state.js';
import { UI } from '../components.js';

export const reportesView = {
  async render(container) {
    const { isStaff } = store.get();

    if (!isStaff) {
      container.innerHTML = UI.emptyState(
        'Acceso Restringido a Personal Bibliotecario',
        'Los reportes estadísticos y análisis de fondos requieren credenciales de Staff o Administrador.'
      );
      return;
    }

    container.innerHTML = UI.loadingSpinner('Procesando informes estadísticos del acervo...');

    try {
      const [librosMas, categoriasTotales, vencidos, sociosMultas, autoresTotales] = await Promise.all([
        reportesService.librosMasPrestados(6),
        reportesService.categoriasTotalLibros(),
        reportesService.prestamosVencidos(),
        reportesService.sociosConMultas(),
        reportesService.autores()
      ]);

      container.innerHTML = `
        <div class="space-y-8 animate-fade-in">

          <div class="pb-4 border-b border-parchment-300">
            <span class="text-xs font-display tracking-widest uppercase text-gold font-bold">Analítica Editorial</span>
            <h2 class="text-2xl sm:text-3xl font-bold font-editorial text-forest">Informes y Estadísticas</h2>
            <p class="text-xs text-warmgray mt-1">Métricas de circulación, libros en mora, distribución por materias e historial de autores.</p>
          </div>

          <!-- FILA 1: LIBROS MÁS PRESTADOS Y CATEGORÍAS -->
          <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">

            <!-- Obras con mayor circulación -->
            <div class="bg-parchment-light p-6 rounded-3xl border border-parchment-300 shadow-sm">
              <h3 class="font-editorial text-lg font-bold text-forest mb-1">Obras con Mayor Rotación</h3>
              <p class="text-xs text-warmgray mb-4">Libros más solicitados por los lectores en sala y domicilio</p>

              <div class="space-y-3">
                ${librosMas.length > 0 ? librosMas.map((l, idx) => `
                  <div class="flex items-center justify-between p-3 bg-ivory rounded-2xl border border-parchment-300">
                    <div class="flex items-center gap-3">
                      <span class="w-6 h-6 rounded-full bg-forest text-parchment-50 font-display text-xs font-bold flex items-center justify-center">
                        ${idx + 1}
                      </span>
                      <div>
                        <h4 class="font-editorial text-sm font-bold text-forest line-clamp-1">${l.titulo}</h4>
                        <p class="text-[11px] text-warmgray">${l.autor}</p>
                      </div>
                    </div>
                    <span class="px-2.5 py-1 rounded-full text-xs font-bold bg-parchment text-forest">
                      ${l.total_prestamos} préstamos
                    </span>
                  </div>
                `).join('') : '<p class="text-xs text-warmgray text-center py-4">Sin datos de préstamos.</p>'}
              </div>
            </div>

            <!-- Distribución por Categorías -->
            <div class="bg-parchment-light p-6 rounded-3xl border border-parchment-300 shadow-sm">
              <h3 class="font-editorial text-lg font-bold text-forest mb-1">Volúmenes por Género</h3>
              <p class="text-xs text-warmgray mb-4">Densidad del catálogo organizada por clasificación temática</p>

              <div class="space-y-3">
                ${categoriasTotales.length > 0 ? categoriasTotales.map(c => `
                  <div class="flex items-center justify-between p-3 bg-ivory rounded-2xl border border-parchment-300">
                    <span class="font-editorial text-sm font-bold text-forest capitalize">${c.nombre}</span>
                    <span class="text-xs font-mono font-bold text-olive">${c.total_libros} títulos</span>
                  </div>
                `).join('') : '<p class="text-xs text-warmgray text-center py-4">Sin categorías registradas.</p>'}
              </div>
            </div>

          </div>

          <!-- FILA 2: PRÉSTAMOS VENCIDOS Y SOCIOS CON MULTAS -->
          <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">

            <!-- Préstamos Vencidos en Alerta -->
            <div class="bg-parchment-light p-6 rounded-3xl border border-parchment-300 shadow-sm">
              <div class="flex items-center justify-between mb-1">
                <h3 class="font-editorial text-lg font-bold text-forest">Préstamos en Mora</h3>
                <span class="px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-amber-50 text-amber-900 border border-amber-200">
                  ${vencidos.length} casos
                </span>
              </div>
              <p class="text-xs text-warmgray mb-4">Obras cuyo plazo reglamentario de entrega ha sido superado</p>

              <div class="space-y-2.5 max-h-72 overflow-y-auto pr-1">
                ${vencidos.length > 0 ? vencidos.map(v => `
                  <div class="p-3 bg-ivory rounded-2xl border border-amber-200 flex items-center justify-between">
                    <div>
                      <h4 class="font-editorial text-sm font-bold text-forest">${v.titulo}</h4>
                      <p class="text-[11px] text-warmgray">${v.socio} (${v.email})</p>
                    </div>
                    <div class="text-right">
                      <span class="text-xs font-bold text-red-700 font-mono">+${v.dias_retraso} días</span>
                      <p class="text-[10px] text-warmgray">Límite: ${v.fecha_limite}</p>
                    </div>
                  </div>
                `).join('') : '<p class="text-xs text-warmgray text-center py-6">¡Excelente! No hay préstamos con mora activa.</p>'}
              </div>
            </div>

            <!-- Socios con multas acumuladas -->
            <div class="bg-parchment-light p-6 rounded-3xl border border-parchment-300 shadow-sm">
              <h3 class="font-editorial text-lg font-bold text-forest mb-1">Socios con Infracciones Pendientes</h3>
              <p class="text-xs text-warmgray mb-4">Usuarios inhabilitados para nuevos préstamos según la regla R11</p>

              <div class="space-y-2.5 max-h-72 overflow-y-auto pr-1">
                ${sociosMultas.length > 0 ? sociosMultas.map(sm => `
                  <div class="p-3 bg-ivory rounded-2xl border border-parchment-300 flex items-center justify-between">
                    <div>
                      <h4 class="font-editorial text-sm font-bold text-forest">${sm.nombre}</h4>
                      <p class="text-[11px] text-warmgray">${sm.total_prestamos} préstamos históricos</p>
                    </div>
                    <span class="text-sm font-bold font-mono text-red-700">$${parseFloat(sm.total_multas).toFixed(2)} adeudados</span>
                  </div>
                `).join('') : '<p class="text-xs text-warmgray text-center py-6">Todos los lectores se encuentran al día en sus multas.</p>'}
              </div>
            </div>

          </div>

          <!-- TABLA RESUMEN POR AUTORES -->
          <div class="bg-parchment-light p-6 rounded-3xl border border-parchment-300 shadow-sm">
            <h3 class="font-editorial text-lg font-bold text-forest mb-1">Rendimiento Bibliográfico por Autor</h3>
            <p class="text-xs text-warmgray mb-4">Total de obras, inventario físico de ejemplares y préstamos acumulados</p>

            <div class="overflow-x-auto">
              <table class="min-w-full divide-y divide-parchment-300 text-xs text-left">
                <thead class="bg-parchment-200 text-forest font-display uppercase tracking-wider text-[11px]">
                  <tr>
                    <th class="px-4 py-3 font-bold">Autor</th>
                    <th class="px-4 py-3 font-bold">Títulos en Catálogo</th>
                    <th class="px-4 py-3 font-bold">Total Ejemplares</th>
                    <th class="px-4 py-3 font-bold">Total Préstamos Históricos</th>
                  </tr>
                </thead>
                <tbody class="divide-y divide-parchment-200 text-warmgray-dark">
                  ${autoresTotales.map(a => `
                    <tr class="hover:bg-parchment-50 transition">
                      <td class="px-4 py-3 font-editorial font-bold text-forest text-sm">${a.nombre}</td>
                      <td class="px-4 py-3 font-mono">${a.total_libros}</td>
                      <td class="px-4 py-3 font-mono">${a.total_ejemplares}</td>
                      <td class="px-4 py-3 font-mono font-bold text-forest">${a.total_prestamos}</td>
                    </tr>
                  `).join('')}
                </tbody>
              </table>
            </div>
          </div>

        </div>
      `;
    } catch (err) {
      container.innerHTML = UI.emptyState('Error cargando reportes', err.message);
    }
  }
};
