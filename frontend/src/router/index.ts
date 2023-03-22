import { createRouter, createWebHistory } from "vue-router";
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
        roles: ["superuser", "user"],
      },
    },
    {
      path: "/conv/:conversation_id",
      name: "conversationHistory",
      component: () => import("@/views/conversation/history-viewer.vue"),
      meta: {
        requiresAuth: true,
        roles: ["superuser", "user"],
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
        {
          path: "/error/404",
          name: "404",
          component: () => import("@/views/error/404.vue"),
          meta: {
            requiresAuth: false,
            roles: ["superuser", "user"],
          },
        },
      ],
    },
    { path: "/:pathMatch(.*)*", name: "NotFound", redirect: "/error/404" },
  ],
  scrollBehavior() {
    return { top: 0 };
  },
});

createRouteGuard(router);

export default router;
