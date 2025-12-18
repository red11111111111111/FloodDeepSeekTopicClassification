/*
 * @Author: your name
 * @Date: 2021-07-26 09:32:49
 * @LastEditTime: 2022-04-26 09:12:33
 * @LastEditors: Please set LastEditors
 * @Description: In User Settings Edit
 * @FilePath: \web-pc\src\pages\big-screen\store\index.js
 */
import Vuex from "vuex";
import Vue from "vue";
import socket from "@/utils/socket"; // 新增：导入 WebSocket

Vue.use(Vuex);

const modulesFiles = require.context("./modules", true, /\.js$/);
const modules = modulesFiles.keys().reduce((modules, modulePath) => {
  const moduleName = modulePath.replace(/^\.\/(.*)\.\w+$/, "$1");
  const value = modulesFiles(modulePath);
  modules[moduleName] = value.default;
  modules[moduleName].namespaced = true; // 打开命名空间
  return modules;
}, {});

const store = new Vuex.Store({
  modules,
  state: {
    isCrawling: false,
    classifiedData: [],
    pollingInterval: null,
    trainingImage: null,
    categories: [],
  },
  mutations: {
    setCollapsed(state, value) {
      // 原有变异
    },
    SET_CRAWLING(state, status) {
      state.isCrawling = status;
    },
    SET_CLASSIFIED_DATA(state, data) {
      state.classifiedData = data;
    },
    SET_POLLING_INTERVAL(state, interval) {
      state.pollingInterval = interval;
    },
    CLEAR_POLLING_INTERVAL(state) {
      if (state.pollingInterval) {
        clearInterval(state.pollingInterval);
        state.pollingInterval = null;
      }
    },
    SET_TRAINING_IMAGE(state, payload) {
      state.trainingImage = payload;
    },
    SET_CATEGORIES(state, categories) {
      state.categories = categories;
    },
  },
  actions: {
    getUserdata({ commit }) {
      // 原有动作
    },
    fetchClassifiedData({ commit }) {
      // 修改：emit 后返回 Promise，等待响应（使用自定义 resolver）
      return new Promise((resolve, reject) => {
        try {
          socket.emit("get_classified_data", {}, (response) => {
            // 如果 socket 支持 ack 回调
            if (response && response.data) {
              commit("SET_CLASSIFIED_DATA", response.data);
              if (!response.data.length) {
                Vue.prototype.$message.warning(
                  "暂无分类数据，请尝试刷新或运行爬虫"
                );
              }
              resolve(response.data);
            } else {
              const errorMessage = "无有效响应数据";
              Vue.prototype.$message.error("获取数据失败：" + errorMessage);
              commit("SET_CLASSIFIED_DATA", []);
              reject(new Error(errorMessage));
            }
          });
        } catch (error) {
          const errorMessage = error.message || "未知错误";
          Vue.prototype.$message.error("获取数据失败：" + errorMessage);
          commit("SET_CLASSIFIED_DATA", []);
          reject(error);
        }
      });
    },
    fetchCategories({ commit }) {
      // 修改：类似，使用 ack 回调
      return new Promise((resolve, reject) => {
        try {
          socket.emit("get_categories", {}, (response) => {
            const categories = Array.isArray(response.data)
              ? response.data
              : [];
            commit("SET_CATEGORIES", categories);
            if (!categories.length) {
              Vue.prototype.$message.warning("暂无类别数据");
            }
            resolve(categories);
          });
        } catch (error) {
          const errorMessage = error.message || "未知错误";
          reject(new Error(errorMessage));
        }
      });
    },
    stopPolling({ commit, dispatch }) {
      return new Promise((resolve, reject) => {
        try {
          socket.emit("stop_crawl", {}, (response) => {
            commit("CLEAR_POLLING_INTERVAL");
            commit("SET_CRAWLING", false);
            if (response && response.success) {
              Vue.prototype.$message.success("爬虫已停止");
              dispatch("fetchClassifiedData");
              resolve(response);
            } else {
              const errorMessage = response?.error || "未知错误";
              Vue.prototype.$message.error("停止爬虫失败：" + errorMessage);
              reject(new Error(errorMessage));
            }
          });
        } catch (error) {
          const errorMessage = error.message || "未知错误";
          Vue.prototype.$message.error("停止爬虫失败：" + errorMessage);
          reject(error);
        }
      });
    },
    updateTrainingImage({ commit }, payload) {
      commit("SET_TRAINING_IMAGE", payload);
    },
  },
  getters: {
    classifiedData: (state) => state.classifiedData,
    isCrawling: (state) => state.isCrawling,
    trainingImage: (state) => state.trainingImage,
    categories: (state) => state.categories,
  },
});

export default store;
