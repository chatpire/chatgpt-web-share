import { createRouter, createWebHistory } from 'vue-router';

import createRouteGuard from './guard';

const router = createRouter({
  history: createWebHistory(import.meta.env.VITE_ROUTER_BASE),
  routes: [
    {
      path: '/',
      redirect: 'home',
    },
    {
      path: '/home',
      name: 'home',
      component: () => import('@/views/home.vue'),
      meta: {
        requiresAuth: false,
        roles: ['superuser', 'user'],
      },
    },
    {
      path: '/login',
      name: 'login',
      component: () => import('@/views/login/index.vue'),
      meta: {
        requiresAuth: false,
        roles: ['superuser', 'user'],
      },
    },
    {
      path: '/conversation',
      name: 'conversation',
      component: () => import('@/views/conversation/index.vue'),
      meta: {
        requiresAuth: true,
        roles: ['superuser', 'user'],
      },
    },
    {
      path: '/conv/:conversation_id',
      name: 'conversationHistory',
      component: () => import('@/views/conversation/history-viewer.vue'),
      meta: {
        requiresAuth: true,
        roles: ['superuser', 'user'],
      },
    },
    {
      path: '/admin',
      name: 'admin',
      redirect: '/admin/system',
      component: () => import('@/views/admin/index.vue'),
      meta: {
        requiresAuth: true,
        roles: ['superuser'],
      },
      children: [
        {
          path: 'system',
          name: 'systemManagement',
          component: () => import('@/views/admin/pages/system_manager.vue'),
        },
        {
          path: 'user',
          name: 'userManagement',
          component: () => import('@/views/admin/pages/user_manager.vue'),
        },
        {
          path: 'conversation',
          name: 'conversationManagement',
          component: () => import('@/views/admin/pages/conversation_manager.vue'),
        },
        {
          path: 'log',
          name: 'logViewer',
          component: () => import('@/views/admin/pages/log_viewer.vue'),
        },
        {
          path: 'openai_settings',
          name: 'openaiSettings',
          component: () => import('@/views/admin/pages/openai_settings.vue'),
        },
        {
          path: 'config',
          name: 'configManagement',
          component: () => import('@/views/admin/pages/config_manager.vue'),
        },
      ],
    },
    {
      path: '/redirect',
      name: 'redirectWrapper',
      children: [
        {
          path: '/redirect/:path',
          name: 'Redirect',
          component: () => import('@/views/redirect/index.vue'),
          meta: {
            requiresAuth: false,
            roles: ['superuser', 'user'],
          },
        },
      ],
    },
    {
      path: '/error',
      name: 'errorPageWrapper',
      children: [
        {
          path: '/error/403',
          name: '403',
          component: () => import('@/views/error/403.vue'),
          meta: {
            requiresAuth: false,
            roles: ['superuser', 'user'],
          },
        },
        {
          path: '/error/404',
          name: '404',
          component: () => import('@/views/error/404.vue'),
          meta: {
            requiresAuth: false,
            roles: ['superuser', 'user'],
          },
        },
      ],
    },
    { path: '/:pathMatch(.*)*', name: 'NotFound', redirect: '/error/404' },
  ],
  scrollBehavior() {
    return { top: 0 };
  },
});

createRouteGuard(router);

export default router;
