/**
 * CONFIGURACIÓN GLOBAL DE LA APLICACIÓN
 * Define endpoints reales del backend, claves de almacenamiento y constantes.
 */

export const CONFIG = {
  API_BASE_URL: '/api/v1',
  DEFAULT_PAGE_SIZE: 12,
  MAX_PAGE_SIZE: 100,
  STORAGE_KEYS: {
    ACCESS_TOKEN: 'exlibris_access_token',
    REFRESH_TOKEN: 'exlibris_refresh_token',
    USER: 'exlibris_user_profile',
  },
  ROLES: {
    ADMIN: 'admin',
    BIBLIOTECARIO: 'bibliotecario',
    SOCIO: 'socio',
  },
};
