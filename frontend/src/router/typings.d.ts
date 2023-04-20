import 'vue-router';

declare type Role = 'superuser' | 'user';

declare module 'vue-router' {
  interface RouteMeta {
    requiresAuth: boolean; // Whether login is required to access the current page (every route must declare)
    roles: Role[]; // The role of the current page (every route must declare)
    ignoreCache?: boolean; // if set true, the page will not be cached
  }
}
