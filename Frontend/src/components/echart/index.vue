<!-- Echart.vue -->
<template>
  <div
    :id="id"
    :class="className"
    :style="{ height: height, width: width }"
    ref="chartDom"
  />
</template>

<script>
import * as echarts from "echarts";
import { debounce } from "lodash";

export default {
  name: "echart",
  props: {
    className: {
      type: String,
      default: "chart",
    },
    id: {
      type: String,
      default: "chart",
    },
    width: {
      type: String,
      default: "100%",
    },
    height: {
      type: String,
      default: "100%",
    },
    options: {
      type: Object,
      default: () => ({}),
    },
  },
  data() {
    return {
      chart: null,
      resizeHandler: null,
    };
  },
  watch: {
    options: {
      handler(options) {
        if (this.chart) {
          if (options && typeof options === "object") {
            this.chart.setOption(options, true);
          }
        } else {
          this.initChart();
        }
      },
      deep: true,
    },
  },
  mounted() {
    this.initChart();
    this.resizeHandler = debounce(() => {
      if (this.chart) {
        this.chart.resize();
      }
    }, 100);
    window.addEventListener("resize", this.resizeHandler);
  },
  beforeDestroy() {
    if (this.chart) {
      this.chart.dispose();
      this.chart = null;
    }
    if (this.resizeHandler) {
      window.removeEventListener("resize", this.resizeHandler);
    }
  },
  methods: {
    async initChart() {
      if (!this.$refs.chartDom) {
        return;
      }

      // 确保DOM已经渲染
      await this.$nextTick();

      // 检查容器尺寸
      const { width, height } = this.$refs.chartDom.getBoundingClientRect();
      if (width === 0 || height === 0) {
        console.warn(
          `ECharts container has invalid dimensions: ${width}x${height}`
        );
        // 如果尺寸为 0，延迟重试
        setTimeout(() => this.initChart(), 200);
        return;
      }

      // 如果已经有实例，先销毁
      if (this.chart) {
        this.chart.dispose();
      }

      try {
        this.chart = echarts.init(this.$refs.chartDom);
        if (this.options && typeof this.options === "object") {
          this.chart.setOption(this.options, true);
        }
      } catch (error) {
        console.error("Failed to initialize ECharts:", error);
      }
    },
  },
};
</script>

<style>
.chart {
  width: 100%;
  height: 100%;
}
</style>
