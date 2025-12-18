<template>
  <div class="center-bottom">
    <div class="right_top_inner">
      <Echart id="rightTop" :options="option" v-if="pageflag" ref="charts" />
    </div>
  </div>
</template>

<script>
import { graphic } from "echarts";
import data from "./data/classcount.json";
export default {
  name: "CenterBottom",
  data() {
    return {
      option: {},
      pageflag: false,
      timer: null,
      colors: {
        numList1: {
          color: "rgba(9,202,243,.7)",
          areaStyle: {
            color: new graphic.LinearGradient(
              0,
              0,
              0,
              1,
              [
                { offset: 0, color: "rgba(9,202,243,.5)" },
                { offset: 1, color: "rgba(9,202,243,.0)" },
              ],
              false
            ),
          },
        },
        numList2: {
          color: "rgba(9,202,23,.7)",
          areaStyle: {
            color: new graphic.LinearGradient(
              0,
              0,
              0,
              1,
              [
                { offset: 0, color: "rgba(9,202,23,.5)" },
                { offset: 1, color: "rgba(9,202,23,.0)" },
              ],
              false
            ),
          },
        },
        numList3: {
          color: "rgba(255,160,122,.7)",
          areaStyle: {
            color: new graphic.LinearGradient(
              0,
              0,
              0,
              1,
              [
                { offset: 0, color: "rgba(255,160,122,.5)" },
                { offset: 1, color: "rgba(255,160,122,.0)" },
              ],
              false
            ),
          },
        },
        numList4: {
          color: "rgba(9,202,243,.7)",
          areaStyle: {
            color: new graphic.LinearGradient(
              0,
              0,
              0,
              1,
              [
                { offset: 0, color: "rgba(9,202,243,.5)" },
                { offset: 1, color: "rgba(9,202,243,.0)" },
              ],
              false
            ),
          },
        },
        numList5: {
          color: "rgba(255,215,0,.7)",
          areaStyle: {
            color: new graphic.LinearGradient(
              0,
              0,
              0,
              1,
              [
                { offset: 0, color: "rgba(255,215,0,.5)" },
                { offset: 1, color: "rgba(255,215,0,.0)" },
              ],
              false
            ),
          },
        },
        numList6: {
          color: "rgba(138,43,226,.7)",
          areaStyle: {
            color: new graphic.LinearGradient(
              0,
              0,
              0,
              1,
              [
                { offset: 0, color: "rgba(138,43,226,.5)" },
                { offset: 1, color: "rgba(138,43,226,.0)" },
              ],
              false
            ),
          },
        },
        numList7: {
          color: "rgba(0,255,127,.7)",
          areaStyle: {
            color: new graphic.LinearGradient(
              0,
              0,
              0,
              1,
              [
                { offset: 0, color: "rgba(0,255,127,.5)" },
                { offset: 1, color: "rgba(0,255,127,.0)" },
              ],
              false
            ),
          },
        },
        rainfall: {
          color: "#0000FF",
          borderColor: "#FFFFFF",
        },
      },
    };
  },
  props: {
    dataId: {
      type: Number,
      default: 1, // 默认显示1条数据
    },
  },
  mounted() {
    this.getData();
    this.$nextTick(() => {
      if (this.$refs.charts) this.$refs.charts.resize();
    });
  },
  methods: {
    getData() {
      this.pageflag = true;
      let categoryData = data.find((item) => item.categoryName == "主题演化");
      if (!categoryData || !categoryData.list) {
        console.error("数据未找到或格式错误");
        return;
      }
      let list = categoryData.list; // 获取原始191条数据

      // 验证原始数据
      console.log("原始数据点数:", list.length);
      if (list.length !== 191) {
        console.warn("预期191条数据，实际", list.length);
      }

      // 压缩到101条
      const targetCount = 101;
      const step = (list.length - 1) / (targetCount - 1); // 步长约1.9
      let compressedList = [];
      for (let i = 0; i < targetCount; i++) {
        const index = Math.round(i * step);
        if (index < list.length) {
          compressedList.push(list[index]);
        }
      }
      // 确保最后时间点为2021-07-24 23:00
      if (
        list[list.length - 1] &&
        list[list.length - 1].time === "2021-07-24 23:00"
      ) {
        compressedList[targetCount - 1] = list[list.length - 1];
      }

      let o = {
        dateList: [],
        seriesData: [],
        numList1: [],
        numList2: [],
        numList3: [],
        numList4: [],
        numList5: [],
        numList6: [],
        numList7: [],
        rainfallList: [],
      };

      // 使用dataId控制显示条数
      compressedList.slice(0, this.dataId).forEach((item) => {
        o.dateList.push(item.time);
        let itemList = item["topic-num"] || [];
        for (let index = 0; index < Math.min(itemList.length, 7); index++) {
          let numList = "numList" + (index + 1);
          o[numList].push(itemList[index] || 0);
          o.seriesData.push(itemList[index] || 0);
        }
        o.rainfallList.push(item.rainfall || 0);
      });

      console.log("当前dataId:", this.dataId);
      console.log("显示数据点数:", o.dateList.length);
      console.log(
        "时间范围:",
        o.dateList[0],
        "到",
        o.dateList[o.dateList.length - 1]
      );
      console.log(
        "降雨量样本:",
        o.rainfallList.slice(0, 5),
        "...",
        o.rainfallList.slice(-5)
      );

      this.init(o.dateList, o);
      this.$nextTick(() => {
        if (this.$refs.charts) this.$refs.charts.resize();
      });
    },

    init(xData, seriesData) {
      // 主题名称顺序（必须与 topic-num 顺序一致）
      const TOPIC_NAMES = [
        this.$t("centerBottom.topic.rescue"),        // 救援类
        this.$t("centerBottom.topic.blessing"),      // 祈福祝愿类
        this.$t("centerBottom.topic.help"),          // 求助类
        this.$t("centerBottom.topic.irrelevant"),    // 无关类
        this.$t("centerBottom.topic.warning"),       // 预警类
        this.$t("centerBottom.topic.disaster"),      // 灾情类
        this.$t("centerBottom.topic.guide"),         // 指南类
      ];


      this.option = {
        legend: {
          data: [...TOPIC_NAMES, this.$t("centerBottom.topic.rainfall")], // 使用扩展运算符将 TOPIC_NAMES 展开
          textStyle: { color: "#7EB7FD" },
          top: "0",
        },
        xAxis: {
          type: "category",
          data: xData,
          boundaryGap: true,
          splitLine: {
            show: true,
            lineStyle: {
              color: "rgba(31,99,163,.2)",
            },
          },
          axisLine: {
            lineStyle: {
              color: "rgba(31,99,163,.1)",
            },
          },
          axisLabel: {
            color: "#7EB7FD",
            fontWeight: "500",
            rotate: 45,
            interval: 9, // 每10条一个标签
            showMinLabel: true,
            showMaxLabel: true,
          },
        },
        yAxis: [
          {
            type: "value",
            name: "微博数量",
            splitLine: {
              show: true,
              lineStyle: {
                color: "rgba(31,99,163,.2)",
              },
            },
            axisLine: {
              lineStyle: {
                color: "rgba(31,99,163,.1)",
              },
            },
            axisLabel: {
              color: "#7EB7FD",
              fontWeight: "500",
            },
          },
          {
            type: "value",
            name: "降雨量 (mm)",
            position: "right",
            min: 0,
            max: 5,
            splitLine: { show: false },
            axisLine: {
              lineStyle: {
                color: "rgba(31,99,163,.1)",
              },
            },
            axisLabel: {
              color: "#7EB7FD",
              fontWeight: "500",
            },
          },
        ],
        tooltip: {
          trigger: "axis",
          backgroundColor: "rgba(0,0,0,.6)",
          borderColor: "rgba(147, 235, 248, .8)",
          textStyle: {
            color: "#FFF",
          },
        },
        grid: {
          show: true,
          left: "40px",
          right: "40px",
          bottom: "80px",
          top: "40px",
          containLabel: true,
          borderColor: "#1F63A3",
        },
        series: [],
      };
      for (let i = 0; i < 7; i++) {
        const key = `numList${i + 1}`;
        const data = seriesData[key] || [];
        this.option.series.push({
          name: TOPIC_NAMES[i], // ✅ 关键：使用语义化名称
          type: "line",
          smooth: true,
          symbol: "none",
          data: data,
          color: this.colors[key].color,
          areaStyle: this.colors[key].areaStyle,
          yAxisIndex: 0,
        });
      }
      this.option.series.push({
        data: seriesData.rainfallList,
        type: "bar",
        name: "降雨量",
        color: this.colors.rainfall.color,
        barWidth: 8,
        borderWidth: 1,
        borderColor: this.colors.rainfall.borderColor,
        yAxisIndex: 1,
      });
    },
  },
  watch: {
    dataId(newVal) {
      this.getData();
    },
    '$i18n.locale': function() {
      this.getData(); // 监听语言变化，重新获取数据
    }
  },
  
};
</script>

<style lang="scss" scoped>
.right_top_inner {
  height: 350px;
  margin-top: -8px;
}
</style>
