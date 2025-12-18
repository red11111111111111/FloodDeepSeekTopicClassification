<template>
  <div class="chart-container" ref="chartContainer">
    <div v-if="loading" class="loading">加载中...</div>
    <div v-else-if="errorMessage" class="error-message">{{ errorMessage }}</div>
    <div v-else-if="!categoryData.length" class="empty-message">暂无数据</div>
    <div id="category-chart" style="width: 100%; height: 100%" v-else></div>
  </div>
</template>

<script>
import * as echarts from "echarts";
import socket from "@/utils/socket";

const CHINESE_TO_KEY = {
  指南: "guide",
  祈福祝愿: "blessing",
  救援: "rescue",
  求助: "help",
  无关: "irrelevant",
  预警: "warning",
  灾情: "disaster",
};

export default {
  name: "CategoryChart",
  data() {
    return {
      chart: null,
      categoryData: [],
      categories: [],
      loading: false,
      errorMessage: "",
      pendingCategories: [],
      fetchTimeout: null,
      resizeObserver: null, // 添加ResizeObserver
    };
  },
  mounted() {
    this.$nextTick(() => {
      this.setupResizeObserver();
      this.initChart();
      this.fetchCategoryData();
    });

    socket.on("categories", this.handleCategories);
    socket.on("classified_data", this.handleClassifiedData);

    // 👇 监听语言切换，重新渲染图表
    this.unwatchLocale = this.$watch("$i18n.locale", () => {
      if (this.categoryData.length > 0) {
        this.updateChart();
      }
    });
  },
  beforeUnmount() {
    this.cleanupResources();
    if (this.unwatchLocale) {
      this.unwatchLocale();
    }
  },
  methods: {
    // 初始化图表（增强版）
    initChart() {
      const chartDom = document.getElementById("category-chart");
      if (!chartDom) {
        console.warn("图表容器未就绪，延迟初始化");
        setTimeout(() => this.initChart(), 300);
        return;
      }

      // 确保容器有有效尺寸
      if (chartDom.offsetWidth <= 0 || chartDom.offsetHeight <= 0) {
        console.warn("容器尺寸无效，延迟初始化");
        setTimeout(() => this.initChart(), 300);
        return;
      }

      try {
        this.chart = echarts.init(chartDom);
        console.log("ECharts初始化成功");
        // 如果已有数据，立即渲染
        if (this.categoryData.length > 0) {
          this.updateChart();
        }
      } catch (error) {
        console.error("ECharts初始化失败:", error);
        setTimeout(() => this.initChart(), 500);
      }
    },

    // 设置ResizeObserver监听容器尺寸变化
    setupResizeObserver() {
      if (this.resizeObserver) return;

      const container = this.$refs.chartContainer;
      if (!container) return;

      this.resizeObserver = new ResizeObserver(() => {
        if (this.chart) {
          this.chart.resize();
        } else {
          this.initChart();
        }
      });

      this.resizeObserver.observe(container);
    },

    // 处理分类数据
    handleCategories(res) {
      console.log("[Socket] 收到 categories:", res);
      this.categories = Array.isArray(res?.data) ? res.data : [];

      if (this.categories.length > 0) {
        this.fetchCounts();
      } else {
        this.handleError("未获取到有效类别数据");
      }
    },

    handleClassifiedData(res) {
      console.log("[Socket] 收到 classified_data:", res);
      if (!res?.query?.category) {
        console.warn("无效数据格式", res);
        return;
      }

      const chineseName = res.query.category; // 后端返回的中文，如 "指南"
      const key = CHINESE_TO_KEY[chineseName] || chineseName; // 无法映射时 fallback 到原值

      const count = Array.isArray(res.data) ? res.data.length : 0;

      const index = this.categoryData.findIndex((item) => item.key === key);
      if (index !== -1) {
        this.categoryData[index].value = count;
      } else {
        this.categoryData.push({
          key: key, // 用于翻译的 key
          originalName: chineseName, // 原始中文（可选，用于 fallback）
          value: count,
        });
      }

      this.pendingCategories = this.pendingCategories.filter(
        (c) => c !== chineseName
      );

      if (this.pendingCategories.length === 0) {
        this.finalizeData();
      }
    },

    // 数据最终处理
    finalizeData() {
      if (this.fetchTimeout) {
        clearTimeout(this.fetchTimeout);
        this.fetchTimeout = null;
      }

      // 检查数据有效性
      const hasValidData = this.categoryData.some((item) => item.value > 0);

      if (!hasValidData && this.categoryData.length > 0) {
        console.warn("所有分类数据为零，显示占位");
        this.categoryData = this.categoryData.map((item) => ({
          ...item,
          value: 1, // 设置为1保证饼图显示
        }));
      }

      this.updateChart();
      this.loading = false;
    },

    // 获取分类数据
    fetchCategoryData() {
      this.resetState();
      this.loading = true;

      try {
        socket.emit("get_categories", {});
      } catch (error) {
        this.handleError(`请求失败: ${error.message}`);
      }
    },

    // 获取分类统计
    fetchCounts() {
      this.resetState();
      this.loading = true;
      this.pendingCategories = [...this.categories]; // categories 是中文数组

      this.fetchTimeout = setTimeout(() => {
        if (this.pendingCategories.length > 0) {
          this.handleError("数据加载超时，请检查网络连接");
        }
      }, 15000);

      this.categories.forEach((chineseCategory) => {
        socket.emit("get_classified_data", { category: chineseCategory }); // 后端需要中文
      });
    },

    // 更新图表（修改为实心饼图）
    updateChart() {
      if (!this.chart) {
        console.warn("图表未初始化，延迟更新");
        setTimeout(() => this.updateChart(), 300);
        return;
      }

      const translatedData = this.categoryData
        .map((item) => {
          // 尝试翻译；如果 key 不存在于 i18n，就显示原始中文（或 key）
          const translatedName = this.$te(`centerBottom.topic.${item.key}`)
            ? this.$t(`centerBottom.topic.${item.key}`)
            : item.originalName || item.key;

          return {
            name: translatedName,
            value: item.value,
          };
        })
        .sort((a, b) => b.value - a.value);

      const option = {
        title: {
          left: "center",
          textStyle: { color: "#fff" },
        },
        tooltip: {
          trigger: "item",
          formatter: "{b}: {c} ({d}%)",
        },
        series: [
          {
            type: "pie",
            radius: "60%",
            center: ["50%", "50%"],
            avoidLabelOverlap: true,
            itemStyle: { borderRadius: 10 },
            label: {
              show: true,
              formatter: "{b}: {c}",
              color: "#fff",
            },
            emphasis: {
              itemStyle: {
                shadowBlur: 10,
                shadowOffsetX: 0,
                shadowColor: "rgba(0, 0, 0, 0.5)",
              },
            },
            data: translatedData,
            color: [
              "#5470c6",
              "#91cc75",
              "#fac858",
              "#ee6666",
              "#73c0de",
              "#3ba272",
              "#fc8452",
              "#9a60b4",
            ],
          },
        ],
      };

      this.chart.setOption(option, true);
      this.chart.resize();
    },

    // 重置状态
    resetState() {
      this.categoryData = [];
      this.pendingCategories = [];
      this.errorMessage = "";
      clearTimeout(this.fetchTimeout);
      this.fetchTimeout = null;
    },

    // 错误处理
    handleError(msg) {
      this.loading = false;
      this.errorMessage = msg;
      console.error(msg);
    },

    // 资源清理
    cleanupResources() {
      if (this.chart) {
        this.chart.dispose();
        this.chart = null;
      }

      if (this.resizeObserver) {
        this.resizeObserver.disconnect();
        this.resizeObserver = null;
      }

      socket.off("categories", this.handleCategories);
      socket.off("classified_data", this.handleClassifiedData);

      clearTimeout(this.fetchTimeout);
    },
  },
};
</script>

<style lang="scss" scoped>
.chart-container {
  position: relative;
  width: 100%;
  height: 100%;
  min-height: 300px; /* 确保最小高度 */
  background: transparent;
}

#category-chart {
  width: 100%;
  height: 100%;
  min-height: inherit; /* 继承最小高度 */
}

.error-message,
.empty-message,
.loading {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  color: #fff;
  font-size: 16px;
  text-align: center;
  width: 100%;
  padding: 20px;
}

.error-message {
  color: #ff7875;
}
.empty-message {
  color: #69c0ff;
}
</style>
