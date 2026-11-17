/**
 * GESTOR DE ESTADO REACTIVO (STATE STORE)
 * Mantiene el estado de la aplicación, el usuario actual y caches de catálogos.
 */

class StateStore {
  constructor() {
    this.state = {
      currentUser: null,
      activeTab: 'inicio', // 'inicio', 'libros', 'autores', 'categorias', 'socios', 'prestamos', 'reportes', 'usuarios'
      autores: [],
      categorias: [],
      socios: [],
      isStaff: false,
      isAdmin: false,
      isSocio: false,
    };
    this.listeners = new Set();
  }

  get() {
    return this.state;
  }

  setUser(user) {
    this.state.currentUser = user;
    this.state.isAdmin = user?.rol === 'admin';
    this.state.isStaff = user?.rol === 'admin' || user?.rol === 'bibliotecario';
    this.state.isSocio = user?.rol === 'socio';
    this.notify();
  }

  setTab(tab) {
    this.state.activeTab = tab;
    this.notify();
  }

  setAutores(autores) {
    this.state.autores = autores;
    this.notify();
  }

  setCategorias(categorias) {
    this.state.categorias = categorias;
    this.notify();
  }

  setSocios(socios) {
    this.state.socios = socios;
    this.notify();
  }

  subscribe(listener) {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  }

  notify() {
    for (const listener of this.listeners) {
      try {
        listener(this.state);
      } catch (err) {
        console.error('Error en listener de estado:', err);
      }
    }
  }
}

export const store = new StateStore();
