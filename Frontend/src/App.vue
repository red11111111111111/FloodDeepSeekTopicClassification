<template>
  <div id="app">
    <div class="header" v-if="showLanguageSwitch">
      <language-switch />
    </div>
    <keep-alive>
      <router-view v-if="$route.meta.keepAlive"></router-view>
    </keep-alive>
    <router-view v-if="!$route.meta.keepAlive"></router-view>
  </div>
</template>

<script>
import LanguageSwitch from "@/components/LanguageSwitch.vue";

export default {
  components: {
    LanguageSwitch,
  },
  data() {
    return {
      newMessages: [],
      notifyTimer: null,
      notifyInstance: null,
      isDev: process.env.NODE_ENV === "development", // 只在开发模式显示测试按钮
    };
  },
  computed: {
    showLanguageSwitch() {
      return ["/login", "/register"].includes(this.$route.path);
    },
  },
  mounted() {

  },
  methods: {
    // 手动发送几条测试消息
    sendTestMessages() {
      for (let i = 0; i < 3; i++) {
        setTimeout(() => {
          this.$bus.$emit("new-message", {
            screen_name: "测试用户" + (i + 1),
            cleaned_text: "这是第 " + (i + 1) + " 条测试消息",
          });
        }, i * 1000);
      }
    },

    // 关闭通知
    closeNotification() {
      if (this.notifyInstance) {
        this.notifyInstance.close();
        this.notifyInstance = null;
      }
    },
  },
};
</script>

<style lang="scss" scoped>
#app {
  width: 100vw;
  height: 100vh;
}

.header {
  position: fixed;
  top: 20px;
  right: 20px;
  z-index: 1000;
}
</style>
