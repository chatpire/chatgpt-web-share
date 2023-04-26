import type { LocationQueryRaw, Router } from 'vue-router';

import { useUserStore } from '@/store';
import { hasLoginCookie } from '@/utils/auth';

// 确保保持登录状态，并及时更新用户信息
export default function setupUserLoginInfoGuard(router: Router) {
  router.beforeEach(async (to, from, next) => {
    const userStore = useUserStore();
    if (hasLoginCookie()) {
      if (userStore.user != null) {
        next();
      } else {
        try {
          await userStore.fetchUserInfo();
          next();
        } catch (error) {
          console.error(error);
          await userStore.logout();
          if (to.name !== 'login') {
            next({
              name: 'login',
              query: {
                redirect: to.name,
                ...to.query,
              } as LocationQueryRaw,
            });
          } else {
            next();
          }
        }
      }
    } else {
      next();
    }
  });
}
