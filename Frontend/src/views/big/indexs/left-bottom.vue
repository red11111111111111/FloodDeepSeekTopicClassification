<template>
  <div
    v-if="pageflag"
    class="right_center_wrap beautify-scroll-def"
    :class="{ 'overflow-y-auto': !sbtxSwiperFlag }"
  >
    <transition name="fade" mode="out-in">
      <ul class="right_center" key="list">
        <li class="right_center_item" :key="activeIndex">
          <div class="inner_right">
            <div class="dibu"></div>
            <div class="flex">
              <div class="info">
                <span class="labels"
                  >{{ $t("visualization.labels.user") }}：</span
                >
                <span class="contents">
                  {{ truncateText(list[activeIndex].screen_name) }}</span
                >
              </div>
              <div class="info time">
                <span class="labels"
                  >{{ $t("visualization.labels.time") }}：</span
                >
                <span class="contents" style="font-size: 12px">
                  {{ list[activeIndex].created_at }}</span
                >
              </div>
            </div>
            <div class="flex">
              <div class="info">
                <span class="labels"
                  >{{ $t("visualization.labels.content") }}：</span
                >
                <span class="contents ciyao">
                  {{ truncateText(list[activeIndex].cleaned_text || "无") }}</span
                >
              </div>
            </div>
          </div>
        </li>
      </ul>
    </transition>
  </div>
  <Reacquire v-else @onclick="getData" style="line-height: 200px" />
</template>

<script>
import socket from "@/utils/socket";
import Kong from "../../../components/kong.vue";

export default {
  name: "left-bottom",
  components: { Kong },
  data() {
    return {
      list: [],
      pageflag: true,
      activeIndex: 0,
      timer: null,
    };
  },
  props: {
    dataId: {
      type: Number,
      default: 1,
    },
  },
  computed: {
    sbtxSwiperFlag() {
      return this.$store.state.setting.ssyjSwiper;
    },
  },
  watch: {
    sbtxSwiperFlag(newVal) {
      if (!newVal) {
        this.stopTimer();
      } else {
        this.startTimer();
      }
    },
  },
  mounted() {
    this.getData(); // 初始加载数据

    // 监听WebSocket事件
    socket.on("cleaned_data", (res) => {
      if (res && res.data) {
        this.list = res.data;
        this.pageflag = true;
        this.startTimer();
        console.log('Fetched data:', this.list);
      } else {
        this.list = [];
        this.pageflag = false;
        console.error('No data received from socket');
      }
    });
  },
  beforeUnmount() {
    socket.off("cleaned_data");
    this.stopTimer();
  },
  methods: {
    getData() {
      socket.emit("get_cleaned_data", {
        start_date: null,
        end_date: null,
      });
    },
    startTimer() {
      if (this.timer) {
        clearTimeout(this.timer);
      }
      if (this.list.length > 0) {
        this.timer = setTimeout(() => {
          this.activeIndex = (this.activeIndex + 1) % this.list.length;
          this.startTimer();
        }, 2000);
      }
    },
    stopTimer() {
      if (this.timer) {
        clearTimeout(this.timer);
        this.timer = null;
      }
    },
    truncateText(text, maxLength = 100) {
      if (!text) return "无";
      return text.length > maxLength ? text.slice(0, maxLength) + "..." : text;
    },
  },
};
</script>

<style lang="scss" scoped>
/* 原样式保持不变 */
.right_center {
  margin-top: 20px;
  width: 100%;
  height: 100%;

  .right_center_item {
    display: flex;
    align-items: center;
    justify-content: center;
    height: auto;
    padding: 10px;
    font-size: 14px;
    color: #fff;

    .inner_right {
      position: relative;
      height: 100%;
      width: 400px;
      flex-shrink: 0;
      line-height: 1.5;

      .dibu {
        position: absolute;
        height: 2px;
        width: 104%;
        bottom: -12px;
        left: -2%;
        background-size: cover;
      }
    }

    .info {
      margin-top: 10px;
      margin-right: 10px;
      display: flex;
      align-items: center;

      .labels {
        flex-shrink: 0;
        font-size: 12px;
        color: rgba(255, 255, 255, 0.6);
      }

      .zhuyao {
        color: $primary-color;
        font-size: 15px;
      }

      .ciyao {
        margin-top: 10px;
        color: rgba(255, 255, 255, 0.8);
      }

      .warning {
        color: #e6a23c;
        font-size: 15px;
      }
    }
  }
}

.right_center_wrap {
  overflow: hidden;
  width: 100%;
  height: 250px;
}

.overflow-y-auto {
  overflow-y: auto;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.5s;
}
.fade-enter,
.fade-leave-to {
  opacity: 0;
}
</style>