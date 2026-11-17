/**
 * COMPONENTES Y UTILIDADES DE INTERFAZ (UI COMPONENTS)
 * Proporciona modales, alertas, badges, loaders y estados vacíos consistentes con la identidad visual.
 */

export const UI = {
  // Notificaciones Toast elegantes
  toast(title, icon = 'success') {
    if (window.Swal) {
      window.Swal.fire({
        toast: true,
        position: 'top-end',
        showConfirmButton: false,
        timer: 3000,
        timerProgressBar: true,
        icon: icon,
        title: title,
        background: '#FAF8F2',
        color: '#183D32',
        customClass: {
          popup: 'border border-parchment shadow-lg rounded-2xl font-sans'
        }
      });
    } else {
      alert(title);
    }
  },

  // Cuadro de diálogo de confirmación con estética clásica
  async confirm(title, text, confirmText = 'Confirmar', isDestructive = false) {
    if (window.Swal) {
      const res = await window.Swal.fire({
        title: `<span class="font-editorial text-xl font-bold ${isDestructive ? 'text-red-900' : 'text-forest'}">${title}</span>`,
        html: `<p class="text-sm text-warmgray-dark font-sans mt-2">${text}</p>`,
        icon: isDestructive ? 'warning' : 'question',
        showCancelButton: true,
        confirmButtonText: confirmText,
        cancelButtonText: 'Cancelar',
        confirmButtonColor: isDestructive ? '#991b1b' : '#183D32',
        cancelButtonColor: '#77746D',
        background: '#FAF8F2',
        customClass: {
          popup: 'rounded-3xl border border-parchment shadow-2xl p-6 font-sans',
          confirmButton: 'rounded-xl px-4 py-2 font-semibold text-sm shadow-sm',
          cancelButton: 'rounded-xl px-4 py-2 font-semibold text-sm'
        }
      });
      return res.isConfirmed;
    }
    return window.confirm(`${title}\n${text}`);
  },

  // Modal genérico
  openModal(modalId) {
    const el = document.getElementById(modalId);
    if (!el) return;
    el.classList.remove('hidden');
    el.classList.add('flex');
    document.body.style.overflow = 'hidden';
  },

  closeModal(modalId) {
    const el = document.getElementById(modalId);
    if (!el) return;
    el.classList.add('hidden');
    el.classList.remove('flex');
    document.body.style.overflow = '';
  },

  // Indicador de carga (Spinner o Skeleton)
  loadingSpinner(message = 'Consultando archivos de la biblioteca...') {
    return `
      <div class="flex flex-col items-center justify-center py-16 text-forest">
        <div class="relative w-12 h-12">
          <div class="w-12 h-12 rounded-full border-2 border-parchment-300 border-t-forest animate-spin"></div>
          <div class="absolute inset-0 flex items-center justify-center text-gold">
            <i class="fa-solid fa-feather-pointed text-xs"></i>
          </div>
        </div>
        <p class="mt-4 text-xs font-semibold tracking-wider uppercase text-forest-light font-display">${message}</p>
      </div>
    `;
  },

  // Estado vacío refinado
  emptyState(title, description, actionText = null, actionCallback = null) {
    return `
      <div class="text-center py-16 px-4 bg-parchment-50 rounded-3xl border border-dashed border-parchment-300 max-w-lg mx-auto">
        <div class="w-16 h-16 mx-auto mb-4 bg-parchment-200 text-forest rounded-2xl flex items-center justify-center shadow-inner">
          <i class="fa-solid fa-book-bookmark text-2xl text-gold"></i>
        </div>
        <h3 class="font-editorial text-lg font-bold text-forest">${title}</h3>
        <p class="text-xs text-warmgray-dark mt-1.5 leading-relaxed max-w-sm mx-auto">${description}</p>
        ${actionText ? `
          <button onclick="${actionCallback}" class="mt-5 inline-flex items-center gap-2 bg-forest hover:bg-forest-light text-parchment-50 px-4 py-2 rounded-xl text-xs font-semibold transition shadow-sm">
            <i class="fa-solid fa-plus text-gold"></i> ${actionText}
          </button>
        ` : ''}
      </div>
    `;
  },

  // Badge de Estado de Préstamo
  loanBadge(estado) {
    switch (estado?.toLowerCase()) {
      case 'activo':
        return `<span class="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-bold bg-emerald-50 text-emerald-800 border border-emerald-200"><span class="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>Activo</span>`;
      case 'vencido':
        return `<span class="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-bold bg-amber-50 text-amber-900 border border-amber-200"><span class="w-1.5 h-1.5 rounded-full bg-amber-600"></span>Vencido</span>`;
      case 'devuelto':
        return `<span class="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium bg-slate-100 text-slate-600 border border-slate-200"><span class="w-1.5 h-1.5 rounded-full bg-slate-400"></span>Devuelto</span>`;
      default:
        return `<span class="px-2.5 py-0.5 rounded-full text-xs font-medium bg-parchment text-forest">${estado || 'N/A'}</span>`;
    }
  },

  // Badge de Rol de Usuario
  roleBadge(rol) {
    switch (rol?.toLowerCase()) {
      case 'admin':
        return `<span class="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-bold tracking-wider uppercase bg-forest text-parchment-100 border border-gold"><i class="fa-solid fa-crown text-[9px] text-gold"></i> Admin</span>`;
      case 'bibliotecario':
        return `<span class="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-semibold tracking-wider uppercase bg-olive/20 text-forest border border-olive/30"><i class="fa-solid fa-book text-[9px] text-olive"></i> Staff</span>`;
      case 'socio':
        return `<span class="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-medium tracking-wider uppercase bg-parchment text-walnut border border-parchment-300"><i class="fa-solid fa-user text-[9px] text-gold"></i> Socio</span>`;
      default:
        return `<span class="px-2.5 py-0.5 rounded-full text-xs text-warmgray">${rol || 'Visitante'}</span>`;
    }
  },

  // Control de paginación
  renderPagination(total, skip, limit, onPageChangeName) {
    if (total <= limit) return '';

    const totalPages = Math.ceil(total / limit);
    const currentPage = Math.floor(skip / limit) + 1;

    let pagesHtml = '';
    const maxButtons = 5;
    let startPage = Math.max(1, currentPage - 2);
    let endPage = Math.min(totalPages, startPage + maxButtons - 1);
    if (endPage - startPage < maxButtons - 1) {
      startPage = Math.max(1, endPage - maxButtons + 1);
    }

    for (let p = startPage; p <= endPage; p++) {
      const isCurrent = p === currentPage;
      const targetSkip = (p - 1) * limit;
      pagesHtml += `
        <button onclick="${onPageChangeName}(${targetSkip})" class="w-8 h-8 rounded-lg text-xs font-semibold transition ${isCurrent ? 'bg-forest text-parchment-50 shadow-sm' : 'bg-parchment-100 hover:bg-parchment text-forest'}">
          ${p}
        </button>
      `;
    }

    const prevSkip = Math.max(0, skip - limit);
    const nextSkip = skip + limit;

    return `
      <div class="flex items-center justify-between pt-6 border-t border-parchment-300 text-xs text-warmgray-dark">
        <p>Mostrando <span class="font-bold text-forest">${Math.min(skip + 1, total)}</span> a <span class="font-bold text-forest">${Math.min(skip + limit, total)}</span> de <span class="font-bold text-forest">${total}</span> registros</p>
        <div class="flex items-center space-x-1.5">
          <button onclick="${onPageChangeName}(${prevSkip})" ${skip === 0 ? 'disabled' : ''} class="px-3 py-1.5 rounded-lg border border-parchment-300 bg-parchment-50 hover:bg-parchment font-semibold disabled:opacity-40 disabled:cursor-not-allowed">
            <i class="fa-solid fa-chevron-left"></i> Anterior
          </button>
          ${pagesHtml}
          <button onclick="${onPageChangeName}(${nextSkip})" ${nextSkip >= total ? 'disabled' : ''} class="px-3 py-1.5 rounded-lg border border-parchment-300 bg-parchment-50 hover:bg-parchment font-semibold disabled:opacity-40 disabled:cursor-not-allowed">
            Siguiente <i class="fa-solid fa-chevron-right"></i>
          </button>
        </div>
      </div>
    `;
  }
};
