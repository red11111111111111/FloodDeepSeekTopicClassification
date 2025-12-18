<template>
  <ScaleScreen
    :width="1920"
    :height="1080"
    class="scale-wrap"
    :selfAdaption="$store.state.setting.isScale"
  >
    <div class="bg">
      <dv-loading v-if="loading">{{ $t("centermap.loading") }}</dv-loading>
      <div v-else class="host-body">
        <!-- 头部 -->
        <div class="d-flex jc-center title_wrap">
          <div class="zuojuxing"></div>
          <div class="youjuxing"></div>
          <div class="guang"></div>
          <div class="d-flex jc-center">
            <div class="title">
              <span class="title-text">{{ $t("centermenu.title") }}</span>
            </div>
          </div>
          <div class="timers">{{ dateYear }} {{ dateDay }}</div>
        </div>
        <Chart></Chart>
      </div>
    </div>
  </ScaleScreen>
</template>

<script>
import { formatTime } from "../../utils/index";
import ScaleScreen from "@/components/scale-screen/scale-screen.vue";
import Chart from "../big/indexs/index.vue";

export default {
  components: {
    ScaleScreen,
    Chart,
  },
  data() {
    return {
      timing: null,
      loading: true,
      dateDay: null,
      dateYear: null,
      dateWeek: null,
      weekday: [
        this.$t("common.Funday") || "周日",
        this.$t("common.Monday") || "周一",
        this.$t("common.Tuesday") || "周二",
        this.$t("common.Wednesday") || "周三",
        this.$t("common.Thursday") || "周四",
        this.$t("common.Friday") || "周五",
        this.$t("common.Saturday") || "周六",
      ],
    };
  },
  mounted() {
    this.timeFn();
    this.cancelLoading();
  },
  beforeDestroy() {
    clearInterval(this.timing);
  },
  methods: {
    timeFn() {
      this.timing = setInterval(() => {
        this.dateDay = formatTime(new Date(), "HH:mm:ss");
        this.dateYear = formatTime(new Date(), "yyyy-MM-dd");
        this.dateWeek = this.weekday[new Date().getDay()];
      }, 1000);
    },
    cancelLoading() {
      setTimeout(() => {
        this.loading = false;
      }, 500);
    },
  },
};
</script>

<style lang="scss">
@import "./styles/home.scss";
</style>
