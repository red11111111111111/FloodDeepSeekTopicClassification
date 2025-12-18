// src/utils/globalSocket.js
import socket from "@/utils/socket"; // 你原来的 WebSocket 工具

const GlobalSocket = {
  init(Vue, router) {
    socket.on("new_help_message", (msg) => {
      // 触发全局事件
      Vue.prototype.$bus.$emit("new-message", msg);
    });
  },
};

export default GlobalSocket;
