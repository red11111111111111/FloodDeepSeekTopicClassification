import Vue from "vue";
import VueI18n from "vue-i18n";
import en from "@/locales/en";
import zh from "@/locales/zh";

Vue.use(VueI18n);

const i18n = new VueI18n({
  locale: localStorage.getItem("language") || "zh", // 默认语言
  messages: {
    en,
    zh,
  },
});

export default i18n;
