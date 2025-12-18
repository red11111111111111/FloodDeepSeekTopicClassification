<template>
  <div class="language-switch" :class="{ 'login-page': isLoginPage }">
    <el-dropdown @command="handleLanguageChange" trigger="click">
      <span class="el-dropdown-link">
        <i class="el-icon-globe"></i>
        {{ currentLanguage === "zh" ? "中文" : "English" }}
        <i class="el-icon-arrow-down el-icon--right"></i>
      </span>
      <el-dropdown-menu slot="dropdown">
        <el-dropdown-item
          command="zh"
          :class="{ active: currentLanguage === 'zh' }"
        >
          <i class="el-icon-check" v-if="currentLanguage === 'zh'"></i>
          中文
        </el-dropdown-item>
        <el-dropdown-item
          command="en"
          :class="{ active: currentLanguage === 'en' }"
        >
          <i class="el-icon-check" v-if="currentLanguage === 'en'"></i>
          English
        </el-dropdown-item>
      </el-dropdown-menu>
    </el-dropdown>
  </div>
</template>

<script>
export default {
  name: "LanguageSwitch",
  data() {
    return {
      currentLanguage: localStorage.getItem("language") || "zh",
    };
  },
  computed: {
    isLoginPage() {
      return this.$route.path === "/login" || this.$route.path === "/register";
    },
  },
  methods: {
    handleLanguageChange(lang) {
      this.currentLanguage = lang;
      localStorage.setItem("language", lang);
      this.$i18n.locale = lang;
      this.$emit("language-changed", lang);
    },
  },
  created() {
    this.$i18n.locale = this.currentLanguage;
  },
};
</script>

<style scoped>
.language-switch {
  width: 100%;
}

/* 登录/注册页面的特殊样式 */
.language-switch.login-page {
  position: absolute;
  top: 20px;
  right: 20px;
  width: auto;
  z-index: 2;
}

.language-switch.login-page .el-dropdown-link {
  color: #fff !important;
  font-size: 16px;
  padding: 8px 16px;
  background-color: rgba(0, 0, 0, 0.5);
  border-radius: 20px;
  cursor: pointer;
  backdrop-filter: blur(5px);
  -webkit-backdrop-filter: blur(5px);
  transition: all 0.3s ease;
}

.language-switch.login-page .el-dropdown-link:hover {
  background-color: rgba(0, 0, 0, 0.7);
}

/* 普通页面的样式 */
.el-dropdown-link {
  display: flex;
  align-items: center;
  gap: 12px;
  width: 100%;
  font-size: 14px;
}

.el-icon-arrow-down {
  transition: transform 0.3s ease;
  margin-left: auto;
}

.el-dropdown-link:hover .el-icon-arrow-down {
  transform: rotate(180deg);
}

/* 下拉菜单样式 */
:deep(.el-dropdown-menu) {
  background: #fff;
  border: 1px solid rgba(0, 0, 0, 0.1);
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}

:deep(.el-dropdown-menu__item) {
  padding: 8px 16px;
  font-size: 14px;
  display: flex;
  align-items: center;
  gap: 8px;
}

:deep(.el-dropdown-menu__item.active) {
  color: #3498db;
  background-color: rgba(52, 152, 219, 0.1);
}

:deep(.el-dropdown-menu__item:hover) {
  background-color: rgba(52, 152, 219, 0.05);
}

.el-icon-globe {
  font-size: 18px;
}

.el-icon-check {
  color: #3498db;
  font-size: 14px;
}
</style>
