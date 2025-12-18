import Vue from "vue";
import VueRouter from "vue-router";
import Home from "@/views/home/Dashboard.vue";
import Big from "@/views/big";
import Login from "@/components/loginpage/Login.vue";
import Register from "@/components/loginpage/Register.vue";
import MapContent from "@/components/MapContent.vue";
import CategoryContent from "@/components/CategoryContent.vue";
import OnlineClassifyContent from "@/components/OnlineClassifyContent.vue";
import Messages from "@/components/Messages.vue"; // 新增：导入 Messages 组件
import MenuPage from "@/views/menu/index.vue"; // 引入菜单页组件

Vue.use(VueRouter);

const routes = [
  {
    path: "/",
    redirect: "/login",
  },
  {
    path: "/login",
    name: "Login",
    component: Login,
    meta: { keepAlive: false },
  },
  {
    path: "/register",
    name: "Register",
    component: Register,
    meta: { keepAlive: false },
  },
  {
    path: "/menu",
    name: "Menu",
    component: MenuPage, // 这里绑定菜单页
    meta: { requiresAuth: true },
  },
  {
    path: "/dashboard",
    name: "Home",
    component: Home,
    meta: { keepAlive: false, requiresAuth: true },
    children: [
      {
        path: "map",
        name: "Map",
        component: MapContent,
        meta: { keepAlive: false, requiresAuth: true },
      },
      {
        path: "big",
        name: "big",
        component: Big,
        meta: { keepAlive: true, requiresAuth: true },
      },
      {
        path: "category",
        name: "Category",
        component: CategoryContent,
        meta: { keepAlive: false, requiresAuth: true },
      },
      {
        path: "onlineclassify",
        name: "OnlineClassify",
        component: OnlineClassifyContent,
        meta: { keepAlive: false, requiresAuth: true },
      },
      {
        path: "messages",
        name: "Messages",
        component: Messages,
        meta: { keepAlive: false, requiresAuth: true },
      }, // 新增：求助消息路由
    ],
  },
];

const router = new VueRouter({
  // 从 history 模式改为 hash 模式（默认）
  // mode: 'history',  // 注释掉或删除这一行
  routes,
});

// 路由守卫
router.beforeEach((to, from, next) => {
  const token = localStorage.getItem("token");
  if (to.meta.requiresAuth && !token) {
    // 如果需要登录但没有 token，重定向到登录页面
    next("/login");
  } else {
    next();
  }
});

export default router;
