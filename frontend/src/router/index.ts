import { createRouter, createWebHistory } from "vue-router";
import { useLoadingBar } from "naive-ui";
import createRouteGuard from "./guard";

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: "/",
      redirect: "home",
    },
    {
      path: "/home",
      name: "home",
      component: () => import("@/views/home.vue"),
      meta: {
        requiresAuth: false,
        roles: ["superuser", "user"],
      },
    },
    {
      path: "/login",
      name: "login",
      component: () => import("@/views/login/index.vue"),
      meta: {
        requiresAuth: false,
        roles: ["superuser", "user"],
      },
    },
    {
      path: "/conversation",
      name: "conversation",
      component: () => import("@/views/conversation/index.vue"),
      meta: {
        requiresAuth: true,
        roles: ["user"],
      },
    },
    {
      path: "/admin",
      name: "admin",
      component: () => import("@/views/admin/index.vue"),
      meta: {
        requiresAuth: true,
        roles: ["superuser"],
      },
    },
    {
      path: "/redirect",
      name: "redirectWrapper",
      children: [
        {
          path: "/redirect/:path",
          name: "Redirect",
          component: () => import("@/views/redirect/index.vue"),
          meta: {
            requiresAuth: false,
            roles: ["superuser", "user"],
          },
        },
      ],
    },
    {
      path: "/error",
      name: "errorPageWrapper",
      children: [
        {
          path: "/error/403",
          name: "403",
          component: () => import("@/views/error/403.vue"),
          meta: {
            requiresAuth: false,
            roles: ["superuser", "user"],
          },
        },
      ],
    },
  ],
  scrollBehavior() {
    return { top: 0 };
  },
});

createRouteGuard(router);

export default router;
