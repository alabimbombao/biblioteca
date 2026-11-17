/**
 * ORQUESTADOR PRINCIPAL DE LA APLICACIÓN (APP & ROUTER)
 * Inicializa servicios, gestiona autenticación y enruta las vistas.
 */

import { authService } from './services/authService.js';
import { store } from './state.js';
import { UI } from './ui/components.js';

import { dashboardView } from './ui/views/dashboardView.js';
import { librosView } from './ui/views/librosView.js';
import { autoresView } from './ui/views/autoresView.js';
import { categoriasView } from './ui/views/categoriasView.js';
import { sociosView } from './ui/views/sociosView.js';
import { prestamosView } from './ui/views/prestamosView.js';
import { reportesView } from './ui/views/reportesView.js';
import { usuariosView } from './ui/views/usuariosView.js';

class AppRouter {
  constructor() {
    this.container = document.getElementById('main-content-container');
    this.navContainer = document.getElementById('nav-links-container');
    this.userContainer = document.getElementById('user-session-container');
  }

  async init() {
    // 1. Verificar si hay token almacenado y recuperar perfil real
    if (authService.isAuthenticated()) {
      try {
        const user = await authService.getMe();
        store.setUser(user);
      } catch (e) {
        console.warn('Sesión no válida o expirada:', e);
        authService.logout();
        store.setUser(null);
      }
    } else {
      store.setUser(null);
    }

    // 2. Suscribirse a cambios de estado para actualizar la barra de navegación
    store.subscribe((state) => {
      this.renderNav(state);
      this.renderUserSession(state);
    });

    // 3. Render inicial
    this.renderNav(store.get());
    this.renderUserSession(store.get());

    // 4. Cargar vista inicial
    this.navigate('inicio');
  }

  renderNav(state) {
    const { activeTab, isStaff, isAdmin, isSocio } = state;

    const tabs = [
      { id: 'inicio', label: 'Inicio', icon: 'fa-landmark' },
      { id: 'libros', label: 'Libros', icon: 'fa-book-bookmark' },
      { id: 'autores', label: 'Autores', icon: 'fa-feather-pointed' },
      { id: 'categorias', label: 'Categorías', icon: 'fa-tags' },
    ];

    if (isStaff || isSocio) {
      tabs.push({ id: 'socios', label: isSocio ? 'Mi Perfil' : 'Socios', icon: 'fa-users' });
      tabs.push({ id: 'prestamos', label: 'Préstamos', icon: 'fa-hand-holding-hand' });
    }

    if (isStaff) {
      tabs.push({ id: 'reportes', label: 'Reportes', icon: 'fa-chart-pie' });
    }

    if (isAdmin) {
      tabs.push({ id: 'usuarios', label: 'Usuarios', icon: 'fa-user-shield' });
    }

    this.navContainer.innerHTML = tabs.map(tab => {
      const isActive = activeTab === tab.id;
      return `
        <button onclick="window.appRouter.navigate('${tab.id}')" 
                class="px-3 py-2 rounded-xl text-xs font-display uppercase tracking-wider font-bold transition flex items-center gap-2 ${isActive ? 'bg-forest text-parchment-50 shadow-sm border border-gold/40' : 'text-forest hover:bg-parchment-200'}">
          <i class="fa-solid ${tab.icon} ${isActive ? 'text-gold' : 'text-warmgray'} text-[11px]"></i>
          <span>${tab.label}</span>
        </button>
      `;
    }).join('');

    // Menú móvil
    const mobileContainer = document.getElementById('mobile-nav-container');
    if (mobileContainer) {
      mobileContainer.innerHTML = tabs.map(tab => {
        const isActive = activeTab === tab.id;
        return `
          <button onclick="window.appRouter.navigate('${tab.id}')" 
                  class="px-3 py-1.5 rounded-lg text-xs font-display whitespace-nowrap transition ${isActive ? 'bg-forest text-parchment-50 font-bold' : 'text-forest hover:bg-parchment-200'}">
            ${tab.label}
          </button>
        `;
      }).join('');
    }
  }

  renderUserSession(state) {
    const { currentUser } = state;

    if (currentUser) {
      this.userContainer.innerHTML = `
        <div class="flex items-center gap-3">
          <div class="text-right hidden sm:block">
            <p class="text-xs font-bold text-forest leading-none font-mono">${currentUser.email}</p>
            <div class="mt-1">${UI.roleBadge(currentUser.rol)}</div>
          </div>
          <button onclick="window.appRouter.logout()" title="Cerrar Sesión" class="w-9 h-9 rounded-xl bg-parchment hover:bg-red-50 text-warmgray hover:text-red-700 flex items-center justify-center transition border border-parchment-300">
            <i class="fa-solid fa-arrow-right-from-bracket text-xs"></i>
          </button>
        </div>
      `;
    } else {
      this.userContainer.innerHTML = `
        <div class="flex items-center gap-2">
          <button onclick="window.appRouter.abrirModalLogin()" class="bg-forest hover:bg-forest-light text-parchment-50 font-display uppercase tracking-wider text-xs font-bold px-4 py-2 rounded-xl shadow-md transition flex items-center gap-2 border border-gold/30">
            <i class="fa-solid fa-key text-gold"></i> Acceder
          </button>
        </div>
      `;
    }
  }

  async navigate(tabId, params = {}) {
    store.setTab(tabId);
    window.scrollTo({ top: 0, behavior: 'smooth' });

    switch (tabId) {
      case 'inicio':
        await dashboardView.render(this.container);
        break;
      case 'libros':
        if (params.categoria_id) {
          librosView.filtros.categoria_id = params.categoria_id;
        }
        await librosView.render(this.container);
        break;
      case 'autores':
        await autoresView.render(this.container);
        break;
      case 'categorias':
        await categoriasView.render(this.container);
        break;
      case 'socios':
        await sociosView.render(this.container);
        break;
      case 'prestamos':
        await prestamosView.render(this.container, params);
        break;
      case 'reportes':
        await reportesView.render(this.container);
        break;
      case 'usuarios':
        await usuariosView.render(this.container);
        break;
      default:
        await dashboardView.render(this.container);
    }
  }

  abrirModalLogin() {
    const modalHtml = `
      <div id="modal-login-dialog" class="fixed inset-0 z-50 flex items-center justify-center p-4 modal-backdrop">
        <div class="bg-ivory rounded-3xl max-w-md w-full p-6 sm:p-8 shadow-2xl border border-parchment-300 modal-content-panel">
          <div class="flex items-center justify-between pb-4 border-b border-parchment-300">
            <div class="flex items-center gap-2.5">
              <div class="w-10 h-10 rounded-2xl bg-forest text-gold flex items-center justify-center shadow-inner">
                <i class="fa-solid fa-shield-halved text-base"></i>
              </div>
              <div>
                <h3 class="font-editorial text-xl font-bold text-forest">Acceso al Archivo</h3>
                <p class="text-[11px] text-warmgray">Autenticación segura JWT</p>
              </div>
            </div>
            <button onclick="window.appRouter.cerrarModalLogin()" class="text-warmgray hover:text-forest text-xl">&times;</button>
          </div>

          <!-- BOTONES DE ACCESO RÁPIDO DE EVALUACIÓN -->
          <div class="mt-4 p-3 bg-parchment-100 rounded-2xl border border-parchment-300 text-xs">
            <p class="font-display uppercase tracking-widest text-[10px] font-bold text-forest mb-2">⚡ Cuentas de Prueba Preconfiguradas:</p>
            <div class="grid grid-cols-2 gap-2">
              <button onclick="window.appRouter.prellenarLogin('admin@biblioteca.com', 'Admin1234')" class="p-2 rounded-xl bg-ivory hover:bg-forest hover:text-parchment-50 border border-parchment-300 text-left transition group">
                <span class="font-bold text-forest group-hover:text-gold block">👑 Administrador</span>
                <span class="text-[10px] text-warmgray group-hover:text-parchment-200">Control absoluto</span>
              </button>
              <button onclick="window.appRouter.prellenarLogin('bibliotecario@biblioteca.com', 'Biblioteca123')" class="p-2 rounded-xl bg-ivory hover:bg-forest hover:text-parchment-50 border border-parchment-300 text-left transition group">
                <span class="font-bold text-forest group-hover:text-gold block">📖 Bibliotecario</span>
                <span class="text-[10px] text-warmgray group-hover:text-parchment-200">Catálogo y Préstamos</span>
              </button>
            </div>
          </div>

          <form id="form-login-element" onsubmit="window.appRouter.ejecutarLogin(event)" class="mt-4 space-y-4">
            <div>
              <label class="block text-xs font-bold text-forest mb-1">Correo Electrónico *</label>
              <input type="email" id="login-input-email" required placeholder="correo@ejemplo.com" class="w-full px-3 py-2 bg-parchment-50 border border-parchment-300 rounded-xl text-xs text-forest focus:ring-2 focus:ring-forest focus:outline-none">
            </div>

            <div>
              <label class="block text-xs font-bold text-forest mb-1">Contraseña *</label>
              <input type="password" id="login-input-password" required placeholder="••••••••" class="w-full px-3 py-2 bg-parchment-50 border border-parchment-300 rounded-xl text-xs text-forest focus:ring-2 focus:ring-forest focus:outline-none">
            </div>

            <div class="pt-2">
              <button type="submit" class="w-full py-2.5 bg-forest hover:bg-forest-light text-parchment-50 font-display uppercase tracking-wider text-xs font-bold rounded-xl shadow-md transition">
                Ingresar a la Plataforma
              </button>
            </div>
          </form>

          <div class="mt-4 pt-3 border-t border-parchment-300 text-center">
            <button onclick="window.appRouter.abrirModalRegistro()" class="text-xs text-forest hover:text-gold font-semibold transition">
              ¿No tienes cuenta? <span class="underline">Regístrate como socio aquí</span>
            </button>
          </div>
        </div>
      </div>
    `;

    document.getElementById('modal-portal').innerHTML = modalHtml;
  }

  cerrarModalLogin() {
    document.getElementById('modal-portal').innerHTML = '';
  }

  prellenarLogin(email, pass) {
    document.getElementById('login-input-email').value = email;
    document.getElementById('login-input-password').value = pass;
    document.getElementById('form-login-element').requestSubmit();
  }

  async ejecutarLogin(e) {
    e.preventDefault();
    const email = document.getElementById('login-input-email').value.trim();
    const pass = document.getElementById('login-input-password').value;

    try {
      const user = await authService.login(email, pass);
      store.setUser(user);
      this.cerrarModalLogin();
      UI.toast(`Bienvenido, ${user.email} (${user.rol.toUpperCase()})`);
      this.navigate('inicio');
    } catch (err) {
      UI.toast(err.message, 'error');
    }
  }

  abrirModalRegistro() {
    const modalHtml = `
      <div id="modal-registro-dialog" class="fixed inset-0 z-50 flex items-center justify-center p-4 modal-backdrop">
        <div class="bg-ivory rounded-3xl max-w-md w-full p-6 sm:p-8 shadow-2xl border border-parchment-300 modal-content-panel">
          <div class="flex items-center justify-between pb-4 border-b border-parchment-300">
            <div>
              <span class="text-[10px] font-display uppercase tracking-widest text-gold font-bold">Afiliación</span>
              <h3 class="font-editorial text-xl font-bold text-forest">Registro de Socio</h3>
            </div>
            <button onclick="window.appRouter.cerrarModalLogin()" class="text-warmgray hover:text-forest text-xl">&times;</button>
          </div>

          <form onsubmit="window.appRouter.ejecutarRegistro(event)" class="mt-4 space-y-3.5">
            <div>
              <label class="block text-xs font-bold text-forest mb-1">Nombre Completo *</label>
              <input type="text" id="reg-nombre" required placeholder="Ej: Marcela Paz" class="w-full px-3 py-2 bg-parchment-50 border border-parchment-300 rounded-xl text-xs text-forest focus:ring-2 focus:ring-forest focus:outline-none">
            </div>

            <div>
              <label class="block text-xs font-bold text-forest mb-1">Correo Electrónico *</label>
              <input type="email" id="reg-email" required placeholder="correo@ejemplo.com" class="w-full px-3 py-2 bg-parchment-50 border border-parchment-300 rounded-xl text-xs text-forest focus:ring-2 focus:ring-forest focus:outline-none">
            </div>

            <div>
              <label class="block text-xs font-bold text-forest mb-1">Teléfono</label>
              <input type="text" id="reg-telefono" placeholder="+57 3001234567" class="w-full px-3 py-2 bg-parchment-50 border border-parchment-300 rounded-xl text-xs text-forest focus:ring-2 focus:ring-forest focus:outline-none">
            </div>

            <div>
              <label class="block text-xs font-bold text-forest mb-1">Contraseña (mínimo 8 caracteres) *</label>
              <input type="password" id="reg-password" required minlength="8" placeholder="••••••••" class="w-full px-3 py-2 bg-parchment-50 border border-parchment-300 rounded-xl text-xs text-forest focus:ring-2 focus:ring-forest focus:outline-none">
            </div>

            <div class="pt-3">
              <button type="submit" class="w-full py-2.5 bg-forest hover:bg-forest-light text-parchment-50 font-display uppercase tracking-wider text-xs font-bold rounded-xl shadow-md transition">
                Completar Afiliación
              </button>
            </div>
          </form>

          <div class="mt-4 pt-3 border-t border-parchment-300 text-center">
            <button onclick="window.appRouter.abrirModalLogin()" class="text-xs text-forest hover:text-gold font-semibold transition">
              ¿Ya tienes cuenta? Inicia sesión aquí
            </button>
          </div>
        </div>
      </div>
    `;

    document.getElementById('modal-portal').innerHTML = modalHtml;
  }

  async ejecutarRegistro(e) {
    e.preventDefault();
    const nombre = document.getElementById('reg-nombre').value.trim();
    const email = document.getElementById('reg-email').value.trim().toLowerCase();
    const telefono = document.getElementById('reg-telefono').value.trim() || null;
    const password = document.getElementById('reg-password').value;

    try {
      await authService.registro(nombre, email, password, telefono);
      UI.toast('¡Registro exitoso! Por favor inicia sesión.');
      this.abrirModalLogin();
    } catch (err) {
      UI.toast(err.message, 'error');
    }
  }

  async logout() {
    const ok = await UI.confirm('¿Cerrar sesión?', '¿Estás seguro de que deseas salir del panel?');
    if (!ok) return;

    await authService.logout();
    store.setUser(null);
    UI.toast('Sesión cerrada correctamente');
    this.navigate('inicio');
  }
}

// Inicialización global
window.addEventListener('DOMContentLoaded', () => {
  window.appRouter = new AppRouter();
  window.appRouter.init();
});
