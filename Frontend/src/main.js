import Vue from "vue";
import App from "./App.vue";
import router from "./router";
import store from "./store";
import i18n from "./plugins/i18n";
import {
  loading,
  borderBox13,
  digitalFlop,
  capsuleChart,
  borderBox8,
} from "@jiaminghi/data-view";
import ElementUI from "element-ui";
import "element-ui/lib/theme-chalk/index.css";
import axios from "axios";
import * as ECharts from "echarts"; 
import * as echarts from "echarts/core";
import { BarChart, LineChart, PieChart } from "echarts/charts";
import {
  TitleComponent,
  TooltipComponent,
  GridComponent,
  LegendComponent,
} from "echarts/components";
import { CanvasRenderer } from "echarts/renderers";

import Echart from "./components/echart/index.vue";
import ItemWrap from "./components/item-wrap/item-wrap.vue";
import Message from "./components/message/message.vue";
import Reacquire from "./components/reacquire/reacquire.vue";
import Messages from "./components/message/message";
import "vue-easytable/libs/theme-default/index.css";
import "@/assets/css/public.scss";
import "@/assets/css/index.scss";
import * as filters from "@/directives/filters";
import GlobalSocket from "@/utils/globalSocket"; // 引入全局 WebSocket
require("./mock/mock");

Vue.config.productionTip = false;

// 全局事件总线
Vue.prototype.$bus = new Vue();

// ECharts 挂载
Vue.prototype.$echarts = ECharts;
Vue.component("v-chart", ECharts);

// 注册自定义组件
Vue.component("Echart", Echart);
Vue.component("ItemWrap", ItemWrap);
Vue.component("Message", Message);
Vue.component("Reacquire", Reacquire);
Vue.prototype.$Message = Messages;

// ElementUI
Vue.use(ElementUI, { size: "small" });

// DataV
Vue.use(loading);
Vue.use(borderBox13);
Vue.use(borderBox8);
Vue.use(digitalFlop);
Vue.use(capsuleChart);

// 全局过滤器
Object.keys(filters).forEach((k) => Vue.filter(k, filters[k]));

// 路由后处理
router.afterEach((to, from) => {
  if (to.path === "/details") {
    document
      .querySelector("body")
      .setAttribute("style", "background-color: white;");
  }
});

// Axios 挂载
Vue.prototype.$axios = axios;

// ECharts 组件注册
echarts.use([
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent,
  BarChart,
  LineChart,
  PieChart,
  CanvasRenderer,
]);

// 路由守卫
router.beforeEach((to, from, next) => {
  const token = localStorage.getItem("token");
  if (to.matched.some((record) => record.meta.requiresAuth)) {
    if (!token) {
      next({
        path: "/login",
        query: { redirect: to.fullPath },
      });
    } else {
      next();
    }
  } else {
    next();
  }
});

// 初始化 WebSocket
GlobalSocket.init(Vue, router); 


// Vue 实例
new Vue({
  router,
  store,
  i18n,
  render: (h) => h(App),
}).$mount("#app");

window.vm = app;