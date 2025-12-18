<template>
  <div class="menu-container">
    <div class="menu-header">
      <h1>{{ $t("menu.title") }}</h1>
    </div>
    <div class="menu-tools">
      <div class="welcome-text">{{ $t("common.welcome") }}, {{ username }}</div>
      <div class="tool-buttons">
        <el-button class="tool-button" type="text" @click="switchLanguage">
          {{ $t("common.switchLang") }}
        </el-button>
        <el-button class="tool-button" type="text" @click="handleLogout">
          {{ $t("common.logout") }}
        </el-button>
      </div>
    </div>
    <div class="menu-cards">
      <div
        class="card"
        v-for="(item, index) in menuItems"
        :key="index"
        :style="{ backgroundImage: item.background }"
        @click="navigateTo(item.path)"
      >
        <div class="card-content">
          <div class="card-icon"><i :class="item.icon"></i></div>
          <div class="card-title">{{ $t(item.titleKey) }}</div>
          <div class="card-desc">{{ $t(item.descKey) }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: "MenuPage",
  data() {
    return {
      username: localStorage.getItem("username") || "Guest",
      menuItems: [
        {
          titleKey: "menu.helpMap",
          descKey: "menu.helpMapDesc",
          path: "/dashboard/map",
          icon: "el-icon-map-location",
          background: "url('/images/map-bg.jpg')"
        },
        {
          titleKey: "menu.visualScreen",
          descKey: "menu.visualScreenDesc",
          path: "/dashboard/big",
          icon: "el-icon-monitor",
          background: "url('/images/screen-bg.jpg')"
        },
        {
          titleKey: "menu.weiboManage",
          descKey: "menu.weiboManageDesc",
          path: "/dashboard/category",
          icon: "el-icon-s-platform",
          background: "url('/images/weibo-bg.jpg')"
        },
        {
          titleKey: "menu.crawler",
          descKey: "menu.crawlerDesc",
          path: "/dashboard/onlineclassify",
          icon: "el-icon-connection",
          background: "url('/images/crawler-bg.jpg')"
        }
      ]
    };
  },
  methods: {
    navigateTo(path) {
      this.$router.push(path);
    },
    switchLanguage() {
      const currentLang = this.$i18n.locale;
      this.$i18n.locale = currentLang === "zh" ? "en" : "zh";
      localStorage.setItem("language", this.$i18n.locale);
    },
    handleLogout() {
      this.$confirm(this.$t("common.confirmLogout"), this.$t("common.tips"), {
        confirmButtonText: this.$t("common.confirm"),
        cancelButtonText: this.$t("common.cancel"),
        type: "warning",
      })
        .then(() => {
          localStorage.removeItem("token");
          localStorage.removeItem("username");
          this.$router.push("/login");
          this.$message({
            type: "success",
            message: this.$t("messages.logoutSuccess"),
          });
        })
        .catch(() => {});
    },
  },
};
</script>

<style scoped>
html, body {
  margin: 0;
  padding: 0;
  overflow-x: hidden;
}

.menu-container {
  background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%);
  min-height: 100vh;
  padding: 20px;
  display: flex;
  flex-direction: column;
  align-items: center;
  position: relative;
  width: 100%;
  box-sizing: border-box;
}

.menu-header {
  margin: 40px 0 60px;
  text-align: center;
}

.menu-header h1 {
  font-size: 50px;
  font-weight: 800;
  background: linear-gradient(92deg, #0072ff 0%, #00eaff 50%, #01aaff 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  text-shadow: 0 0 20px rgba(0, 234, 255, 0.3);
}

/* 居中显示，固定宽高 */
.menu-cards {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 30px;
  width: 100%;
  max-width: 2200px; /* 控制总宽度，居中 */
  margin: 0 auto;
  padding: 40px 0;
}

/* 卡片固定宽高 */
.card {
  position: relative;
  border-radius: 15px;
  width: 500px;
  height: 1000px;
  background-size: cover;
  background-position: center;
  cursor: pointer;
  overflow: hidden;
  transition: all 0.4s ease;
  display: flex;
  justify-content: center;
  align-items: center;
}

.card::after {
  content: "";
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(to top, rgba(0,0,0,0.7), rgba(0,0,0,0.3));
  z-index: 1;
}

.card-content {
  position: relative;
  z-index: 2;
  text-align: center;
  color: #fff;
}

.card-icon {
  font-size: 50px;
  margin-bottom: 20px;
}

.card-title {
  font-size: 28px;
  font-weight: bold;
  margin-bottom: 15px;
}

.card-desc {
  font-size: 18px;
  opacity: 0.9;
}

/* hover 效果 */
.card:hover {
  transform: translateY(-8px) scale(1.03);
  box-shadow: 0 10px 25px rgba(0,0,0,0.3);
}

/* 右上角工具栏 */
.menu-tools {
  position: absolute;
  top: 20px;
  right: 20px;
  display: flex;
  align-items: center;
  gap: 20px;
}

.welcome-text {
  color: #00eaff;
}

.tool-button {
  color: #00eaff;
  border: 1px solid rgba(0, 234, 255, 0.3);
  border-radius: 20px;
  transition: all 0.3s ease;
}

.tool-button:hover {
  background: rgba(0, 234, 255, 0.1);
  border-color: rgba(0, 234, 255, 0.5);
}
</style>
