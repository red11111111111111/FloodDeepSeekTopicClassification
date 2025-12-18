<template>
  <ul class="user-overview flex" v-if="pageflag">
    <li class="user-overview-item" style="color: #00fdfa">
      <div class="user-overview-nums allnum">
        <dv-digital-flop
          :config="totalConfig"
          style="width: 100%; height: 100%"
        />
      </div>
      <p style="color: rgb(0, 253, 250)">{{ $t("data.totalWeibo") }}</p>
    </li>
    <li class="user-overview-item" style="color: #07f7a8">
      <div class="user-overview-nums normal-users">
        <dv-digital-flop
          :config="normalUsersConfig"
          style="width: 100%; height: 100%"
        />
      </div>
      <p style="color: rgb(7, 247, 168)">{{ $t("data.normalUsers") }}</p>
    </li>
    <li class="user-overview-item" style="color: #e3b337">
      <div class="user-overview-nums official-media">
        <dv-digital-flop
          :config="officialMediaConfig"
          style="width: 100%; height: 100%"
        />
      </div>
      <p style="color: rgb(227, 179, 55)">{{ $t("data.officialMedia") }}</p>
    </li>
  </ul>
</template>

<script>
import socket from "@/utils/socket";
import { mapGetters } from "vuex";

let style = {
  fontSize: 24,
};

export default {
  name: "LeftTop",
  data() {
    return {
      pageflag: true,
      totalWeibo: 0,
      normalUsers: 0,
      officialMedia: 0,
      henanIpCount: 0,
      baseStyle: {
        fontSize: 24,
      },
      timer: null,
      totalConfig: {
        number: [0],
        content: "{nt}",
        style: {
          fontSize: 34,
          fill: "#00fdfa",
        },
      },
      normalUsersConfig: {
        number: [0],
        content: "{nt}",
        style: {
          fontSize: 34,
          fill: "#07f7a8",
        },
      },
      officialMediaConfig: {
        number: [0],
        content: "{nt}",
        style: {
          fontSize: 34,
          fill: "#e3b337",
        },
      },
      henanIpConfig: {
        number: [0],
        content: "{nt}",
        style: {
          fontSize: 34,
          fill: "#f5023d",
        },
      },
    };
  },
  computed: {
    ...mapGetters(["isCrawling"]),
  },
  mounted() {
    this.fetchData();
    this.startPolling();

    // 监听WebSocket事件
    socket.on("weibo_data", (res) => {
      try {
        const data = res.data || [];

        // 计算总数
        this.totalWeibo = data.length;
        this.totalConfig = {
          ...this.totalConfig,
          number: [this.totalWeibo],
        };

        // 统计用户类型
        this.normalUsers = data.filter(
          (item) => item.user_authentication === "普通用户"
        ).length;
        this.normalUsersConfig = {
          ...this.normalUsersConfig,
          number: [this.normalUsers],
        };

        this.officialMedia = data.filter(
          (item) => item.user_authentication !== "普通用户"
        ).length;
        this.officialMediaConfig = {
          ...this.officialMediaConfig,
          number: [this.officialMedia],
        };

        // 统计河南IP
        this.henanIpCount = data.filter((item) => item.ip === "河南").length;
        this.henanIpConfig = {
          ...this.henanIpConfig,
          number: [this.henanIpCount],
        };
        this.pageflag = true;
      } catch (error) {
        let errorMessage = "未知错误";
        if (error.message) {
          errorMessage = error.message;
        }
        this.$message.error("获取数据失败: " + errorMessage);
      }
    });
  },
  beforeUnmount() {
    // 组件销毁前清除定时器
    if (this.timer) {
      clearInterval(this.timer);
      this.timer = null;
    }
    socket.off("weibo_data");
  },
  methods: {
    fetchData() {
      socket.emit("get_weibo_data", {
        start_date: null,
        end_date: null,
      });
    },
    startPolling() {
      // 清除已有定时器
      if (this.timer) {
        clearInterval(this.timer);
        this.timer = null;
      }

      // 只有在爬虫任务开启时才启动轮询
      if (this.isCrawling) {
        this.timer = setInterval(() => {
          this.fetchData();
        }, 10000);
      }
    },
  },
  watch: {
    isCrawling(newVal) {
      // 监听 isCrawling 状态变化，动态控制轮询
      this.startPolling();
    },
  },
};
</script>

<style lang="scss" scoped>
/* 原样式保持不变 */
.flex {
  display: flex;
  justify-content: space-around;
  align-items: center;
}

.user-overview {
  li {
    flex: 1;
    text-align: center;

    p {
      text-align: center;
      height: 16px;
      font-size: 16px;
      margin-top: 10px;
      color: #ffffff;
      opacity: 0.8;
    }

    .user-overview-nums {
      width: 120px;
      height: 120px;
      text-align: center;
      line-height: 120px;
      font-size: 24px;
      margin: 30px auto;
      background-size: cover;
      background-position: center center;
      position: relative;

      &::before {
        content: "";
        position: absolute;
        width: 100%;
        height: 100%;
        top: 7px;
        left: 7px;
        z-index: 0; /* 确保背景在数字下方 */
      }

      &.bgdonghua::before {
        animation: rotating 14s linear infinite;
      }
    }

    .allnum {
      background: linear-gradient(45deg, rgba(0, 253, 250, 0.2), transparent);
    }
    .normal-users {
      background: linear-gradient(45deg, rgba(7, 247, 168, 0.2), transparent);
    }
    .official-media {
      background: linear-gradient(45deg, rgba(227, 179, 55, 0.2), transparent);
    }
    .henan-ip {
      background: linear-gradient(45deg, rgba(245, 2, 61, 0.2), transparent);
    }
  }
}
</style>