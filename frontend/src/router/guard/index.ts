import type { Router } from 'vue-router';
import setupUserLoginInfoGuard from './userLoginInfo';
import setupPermissionGuard from './permission';

export default function createRouteGuard(router: Router) {
  setupUserLoginInfoGuard(router);
  setupPermissionGuard(router);
}
