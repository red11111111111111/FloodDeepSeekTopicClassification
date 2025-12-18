<!--
 * @Author: daidai
 * @Date: 2022-02-28 16:16:42
 * @LastEditors: Please set LastEditors
 * @LastEditTime: 2022-10-25 09:18:22
 * @FilePath: \web-pc\src\pages\big-screen\view\indexs\left-center.vue
-->
<template>
  <Echart
    id="leftCenter"
    :options="options"
    class="left_center_inner"
    v-if="pageflag"
    ref="charts"
  />
  <!-- <Reacquire v-else @onclick="getData" style="line-height:200px">
    重新获取
  </Reacquire> -->
</template>

<script>
import socket from "@/utils/socket";
import { mapGetters } from 'vuex';

export default {
  data() {
    return {
      options: {},
      countUserNumData: {
        totalNum: 0,
        words0: 0,
        words70: 0,
        words140: 0,
      },
      pageflag: true,
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
    ...mapGetters(['isCrawling']),
  },
  mounted() {
    this.getData();
    this.startPolling();

    // 监听WebSocket事件
    socket.on("weibo_data", (res) => {
      try {
        const data = res.data || [];
        this.countUserNumData.totalNum = data.length;
        this.countUserNumData.words0 = data.filter((item) => {
          const length = item.text ? item.text.length : 0;
          return length >= 0 && length <= 70;
        }).length;
        this.countUserNumData.words70 = data.filter((item) => {
          const length = item.text ? item.text.length : 0;
          return length > 70 && length <= 140;
        }).length;
        this.countUserNumData.words140 = data.filter((item) => {
          const length = item.text ? item.text.length : 0;
          return length > 140;
        }).length;
        this.pageflag = true;
        this.init();
      } catch (error) {
        let errorMessage = "未知错误";
        if (error.message) {
          errorMessage = error.message;
        }
        this.$message.error("获取数据失败: " + errorMessage);
        this.pageflag = false;
      }
    });
  },
  beforeUnmount() {
    if (this.timer) {
      clearInterval(this.timer);
      this.timer = null;
    }
    socket.off("weibo_data");
  },
  methods: {
    getData() {
      socket.emit("get_weibo_data", {
        start_date: null,
        end_date: null,
      });
    },
    startPolling() {
      if (this.timer) {
        clearInterval(this.timer);
        this.timer = null;
      }
      if (this.isCrawling) {
        this.timer = setInterval(() => {
          this.getData();
        }, 10000);
      }
    },
    init() {
      let total = this.countUserNumData.totalNum;
      let colors = ["#ECA444", "#33A1DB", "#56B557"];
      let piedata = {
        name: "用户总览",
        type: "pie",
        radius: ["42%", "65%"],
        avoidLabelOverlap: false,
        itemStyle: {
          borderRadius: 4,
          borderColor: "rgba(0,0,0,0)",
          borderWidth: 2,
        },
        color: colors,
        data: [
          {
            value: this.countUserNumData.words0,
            name: "(0,70]",
            label: { shadowColor: colors[0] },
          },
          {
            value: this.countUserNumData.words70,
            name: "[71-140]",
            label: { shadowColor: colors[2] },
          },
          {
            value: this.countUserNumData.words140,
            name: "(140,+∞)",
            label: { shadowColor: colors[1] },
          },
        ],
      };
      this.options = {
        title: {
          text: ["{value|" + total + "}"].join("\n"),
          top: "center",
          left: "center",
          textStyle: {
            rich: {
              value: { color: "#ffffff", fontSize: 24, fontWeight: "bold", lineHeight: 20 },
              name: { color: "#ffffff", lineHeight: 20 },
            },
          },
        },
        tooltip: {
          trigger: "item",
          backgroundColor: "rgba(0,0,0,.6)",
          borderColor: "rgba(147, 235, 248, .8)",
          textStyle: { color: "#FFF" },
        },
        legend: { show: false, top: "5%", left: "center" },
        series: [
          {
            ...piedata,
            tooltip: { show: true },
            label: {
              formatter: "   {b|{b}}   \n   {c|{c}}   {per|{d}%}  ",
              rich: {
                b: { color: "#fff", fontSize: 12, lineHeight: 26 },
                c: { color: "#31ABE3", fontSize: 14 },
                per: { color: "#31ABE3", fontSize: 14 },
              },
            },
            labelLine: { length: 20, length2: 36, show: true },
            emphasis: { show: true },
          },
          {
            ...piedata,
            tooltip: { show: true },
            itemStyle: {},
            label: {
              backgroundColor: "inherit",
              height: 0,
              width: 0,
              lineHeight: 0,
              borderRadius: 2.5,
              shadowBlur: 8,
              shadowColor: "auto",
              padding: [2.5, -2.5, 2.5, -2.5],
            },
            labelLine: { length: 20, length2: 36, show: false },
          },
        ],
      };
    },
  },
  watch: {
    isCrawling(newVal) {
      this.startPolling();
    },
  },
};
</script>

<style lang="scss" scoped>
/* 原样式保持不变 */
.left_center_inner {
  width: 100%;
  height: 100%;
}
</style>