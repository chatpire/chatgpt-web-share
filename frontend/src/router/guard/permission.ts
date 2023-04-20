import type { LocationQueryRaw, Router } from 'vue-router';

import { i18n } from '@/i18n';
import { useUserStore } from '@/store';
import { Message } from '@/utils/tips';
const t = i18n.global.t as any;

// 在 userLoginInfo 之后，此时要么登录成功，要么未登录
export default function setupPermissionGuard(router: Router) {
  router.beforeEach(async (to, from, next) => {
    const userStore = useUserStore();
    if (!to.meta.requiresAuth) next();
    else {
      if (userStore.user === null) {
        Message.error(t('errors.userNotLogin'));
        next({
          name: 'login',
          query: {
            redirect: to.name,
            ...to.query,
          } as LocationQueryRaw,
        });
      } else {
        // if (to.meta.roles.find((role) => role === userStore.user.role) === ) {
        //   if (userStore.user.is_superuser) next();
        //   else next({ name: "403" });
        // } else next();
        const role = userStore.user.is_superuser ? 'superuser' : 'user';
        if (to.meta.roles.find((r) => r === role) === undefined) {
          next({ name: '403' });
        } else next();
      }
    }
  });
}
