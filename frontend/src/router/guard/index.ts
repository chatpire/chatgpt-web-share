import type { Router } from 'vue-router';

import setupPermissionGuard from './permission';
import setupUserLoginInfoGuard from './userLoginInfo';

export default function createRouteGuard(router: Router) {
  setupUserLoginInfoGuard(router);
  setupPermissionGuard(router);
}
