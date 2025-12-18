<template>
  <div class="app-container">
    <!-- 侧边栏菜单 -->
    <div class="sidebar">
      <!-- 上半区域：用户信息和退出按钮 -->
      <div class="sidebar-header">
        <div class="user-info">
          <i class="el-icon-user-solid avatar-icon"></i>
          <div class="user-details">
            <div class="welcome-text">{{ $t("common.welcome") }}</div>
            <div class="username-text">{{ username }}</div>
          </div>
        </div>
        <el-button type="text" @click="handleLogout" class="logout-btn">
          <i class="el-icon-switch-button"></i>
          <span>{{ $t("common.logout") }}</span>
        </el-button>
      </div>
      <!-- 下半区域：菜单项 -->
      <el-menu
        :default-active="activeMenu"
        class="sidebar-menu"
        @select="handleMenuSelect"
        background-color="#2c3e50"
        text-color="#ecf0f1"
        active-text-color="#3498db"
      >
        <el-menu-item index="/dashboard/map">
          <i class="el-icon-map-location"></i>
          <span slot="title">{{ $t("menu.map") }}</span>
        </el-menu-item>
        <el-menu-item index="/dashboard/big">
          <i class="el-icon-monitor"></i>
          <span slot="title">{{ $t("menu.visualization") }}</span>
        </el-menu-item>
        <el-menu-item index="/dashboard/category">
          <i class="el-icon-menu"></i>
          <span slot="title">{{ $t("menu.category") }}</span>
        </el-menu-item>
        <el-menu-item index="/dashboard/onlineclassify">
          <i class="el-icon-connection"></i>
          <span slot="title">{{ $t("menu.crawler") }}</span>
        </el-menu-item>
        <!-- 新增：求助消息菜单项 -->
        <el-menu-item index="/dashboard/messages">
          <i class="el-icon-message"></i>
          <span slot="title">{{ $t("menu.messages") }}</span>
        </el-menu-item>
        <div class="language-menu-container">
          <language-switch />
        </div>
      </el-menu>
    </div>

    <!-- 主要内容区域 -->
    <div class="content">
      <el-card class="content-card">
        <transition name="fade">
          <router-view></router-view>
        </transition>
      </el-card>
    </div>
  </div>
</template>

<script>
import socket from "@/utils/socket";
import LanguageSwitch from "@/components/LanguageSwitch.vue";

export default {
  components: {
    LanguageSwitch,
  },
  data() {
    return {
      username: localStorage.getItem("username") || "用户",
      activeMenu: "/map",
    };
  },
  methods: {
    handleMenuSelect(path) {
      this.activeMenu = path;
      if (this.$route.path !== path) {
        this.$router.push(path).catch(() => {});
      }
      // 如果点击消息菜单，清空新消息提示（保留此逻辑但移除轮询相关）
      if (path === "/dashboard/messages") {
        // 注意：原newMessagesCount变量已移除，如需清空提示需在其他地方处理
      }
    },
    handleLogout() {
      localStorage.removeItem("token");
      localStorage.removeItem("username");
      this.$message.success(this.$t("messages.logoutSuccess"));
      this.$router.push("/login");
    },
  },
  watch: {
    "$route.path"(newPath) {
      this.activeMenu = newPath;
    },
  },
  mounted() {
    // 仅保留路由初始化逻辑，移除轮询相关监听
    if (this.$route.path === "/dashboard") {
      this.activeMenu = "/map";
      this.$router.push("/map").catch(() => {});
    } else {
      this.activeMenu = this.$route.path;
    }
  },
  beforeUnmount() {
    // 移除轮询相关的清理代码
    socket.off("help_locations"); // 保留原清理逻辑（如果有其他监听需要保留）
  },
};
</script>

<style scoped>
/* 样式保持不变，移除了与轮询相关的动态样式 */
.app-container {
  display: flex;
  height: 100vh;
  background-color: #f4f6f9;
}

.sidebar {
  width: 210px;
  height: 100%;
  background: linear-gradient(180deg, #2c3e50 0%, #34495e 100%);
  border-right: 1px solid rgba(230, 230, 230, 0.1);
  display: flex;
  flex-direction: column;
  box-shadow: 2px 0 10px rgba(0, 0, 0, 0.1);
}

.sidebar-header {
  padding: 20px;
  background: rgba(0, 0, 0, 0.2);
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.user-info {
  display: flex;
  align-items: center;
  margin-bottom: 15px;
  padding-bottom: 15px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.avatar-icon {
  font-size: 24px;
  width: 40px;
  height: 40px;
  background: rgba(52, 152, 219, 0.2);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #3498db;
  margin-right: 12px;
}

.user-details {
  flex: 1;
}

.welcome-text {
  font-size: 12px;
  color: #95a5a6;
  margin-bottom: 4px;
}

.username-text {
  font-size: 16px;
  font-weight: 600;
  color: #fff;
  letter-spacing: 0.5px;
}

.logout-btn {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 8px 16px;
  background: rgba(231, 76, 60, 0.1);
  border-radius: 6px;
  transition: all 0.3s ease;
}

.logout-btn:hover {
  background: rgba(231, 76, 60, 0.2);
  color: #e74c3c;
  transform: translateY(-1px);
}

.logout-btn i {
  margin-right: 8px;
  font-size: 16px;
}

.logout-btn span {
  font-size: 14px;
}

.sidebar-menu {
  flex: 1;
  border-right: none;
  padding-top: 10px;
}

.content {
  flex: 1;
  overflow-y: hidden;
}

.content-card {
  margin: 0;
  padding: 0;
  background-color: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  display: flex;
  flex-direction: column;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.1s ease;
}

.fade-enter,
.fade-leave-to {
  opacity: 0;
}

.el-menu-item {
  height: 56px;
  line-height: 56px;
  margin: 8px 0;
  padding-left: 20px !important;
  margin-right: 9px;
  transition: all 0.3s ease;
}

.el-menu-item:hover {
  background: rgba(52, 152, 219, 0.1) !important;
  color: #3498db !important;
}

.el-menu-item.is-active {
  background: linear-gradient(
    90deg,
    rgba(52, 152, 219, 0.2),
    rgba(52, 152, 219, 0.1)
  ) !important;
  border-left: 4px solid #3498db;
}

.el-menu-item i {
  margin-right: 12px;
  font-size: 18px;
  transition: all 0.3s ease;
}

.el-menu-item:hover i {
  transform: scale(1.3);
  color: #3498db;
}

.language-menu-container {
  margin-top: auto;
  padding: 0 20px 16px;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
}

.language-switch .el-dropdown-link {
  color: #b4bccc !important;
  padding: 12px 16px;
  border-radius: 6px;
  transition: all 0.3s ease;
}

.language-switch .el-dropdown-link:hover {
  background: rgba(255, 255, 255, 0.08);
  color: #3498db !important;
}

.language-switch .el-icon-globe {
  color: inherit;
  font-size: 18px;
}

.language-switch .el-icon-arrow-down {
  color: inherit;
  margin-left: auto;
  font-size: 14px;
}

.language-switch .el-dropdown-menu {
  background: #2c3e50;
  border: 1px solid rgba(255, 255, 255, 0.1);
  min-width: 120px;
}

.language-switch .el-dropdown-menu__item {
  color: #ecf0f1;
  background: transparent;
  padding: 10px 20px;
}

.language-switch .el-dropdown-menu__item:hover {
  background: rgba(52, 152, 219, 0.2) !important;
}

.language-switch .el-dropdown-menu__item.active {
  background: rgba(52, 152, 219, 0.15) !important;
}

.language-switch .el-icon-check {
  color: #3498db;
}
</style>