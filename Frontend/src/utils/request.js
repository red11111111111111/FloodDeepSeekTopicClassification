import axios from "axios";

const instance = axios.create({
  baseURL: "http://localhost:5004", // 修改为正确的端口
  timeout: 5000, // 增加超时时间
  headers: {
    "Content-Type": "application/json",
  },
});

// 添加请求拦截器
instance.interceptors.request.use(
  (config) => {
    // 添加 token
    const token = localStorage.getItem("token");
    if (token) {
      config.headers["Authorization"] = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// 添加响应拦截器
instance.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    // 处理错误响应
    if (error.response) {
      // 有响应但状态码不在 2xx 范围内
      const errorMessage = error.response.data.message || "请求失败";
      return Promise.reject({
        ...error,
        message: errorMessage,
      });
    } else if (error.request) {
      // 请求已发出但没有收到响应
      return Promise.reject({
        ...error,
        message: "无法连接到服务器",
      });
    } else {
      // 请求设置时出错
      return Promise.reject({
        ...error,
        message: "请求配置错误",
      });
    }
  }
);

export default instance;
