<template>
  <div class="right_bottom">
    <v-chart class="chart" :options="chartOption" autoresize />
  </div>
</template>

<script>
import VChart from "@/components/echart/index.vue";
import "echarts";

export default {
  name: "RightCenter",
  components: {
    VChart,
  },
  data() {
    return {
      chartOption: {
        title: {
          text: "",
          left: "center",
          top: 20,
          textStyle: {
            fontSize: 16,
            fontWeight: "bold",
          },
        },
        tooltip: {
          trigger: "axis",
          axisPointer: { type: "shadow" },
          formatter: function (params) {
            let result = `${params[0].name}<br/>`;
            params.forEach((param) => {
              result += `${param.seriesName}: ${(param.value * 100).toFixed(
                2
              )}%<br/>`;
            });
            return result;
          },
        },
        legend: {
          top: "10%",
          textStyle: {
            fontSize: 12,
          },
        },
        grid: {
          top: "20%",
          left: "3%",
          right: "4%",
          bottom: "3%",
          containLabel: true,
        },
        xAxis: {
          type: "category",
          data: [],
          axisLabel: {
            interval: 0,
            rotate: 30,
          },
        },
        yAxis: {
          type: "value",
          max: 1,
          min: 0,
          axisLabel: {
            formatter: function (value) {
              return (value * 100).toFixed(0) + "%";
            },
          },
        },
        series: [],
        animation: true,
        animationDuration: 1000,
        animationEasing: "cubicOut",
      },
    };
  },
  watch: {
    "$store.state.trainingImage": {
      handler(newTrainingImage) {
        if (newTrainingImage && newTrainingImage.isComparison) {
          this.updateChart(newTrainingImage.metrics);
        } else {
          this.resetChart();
        }
      },
      deep: true,
      immediate: true,
    },
  },
  methods: {
    updateChart(metrics) {
      if (!metrics) {
        console.log("No metrics provided, resetting chart");
        this.resetChart();
        return;
      }

      console.log("Updating chart with metrics:", metrics);

      const xAxisData = metrics.metrics || [
        "Accuracy",
        "Precision",
        "Recall",
        "F1-Score",
      ];
      const model1Data = metrics.model1_data || [];
      const model2Data = metrics.model2_data || [];
      const model1Name = metrics.model1_name || "Model 1";
      const model2Name = metrics.model2_name || "Model 2";

      // 确保数据长度匹配
      if (
        model1Data.length !== xAxisData.length ||
        model2Data.length !== xAxisData.length
      ) {
        console.error("Data length mismatch:", {
          xAxisData,
          model1Data,
          model2Data,
        });
        this.resetChart();
        return;
      }

      this.chartOption.xAxis.data = xAxisData;
      this.chartOption.series = [
        {
          name: model1Name,
          type: "bar",
          data: model1Data,
          barWidth: "35%",
          itemStyle: { color: "#5470C6" },
        },
        {
          name: model2Name,
          type: "bar",
          data: model2Data,
          barWidth: "35%",
          itemStyle: { color: "#91CC75" },
        },
      ];

      console.log("Updated chartOption:", this.chartOption);
    },
    resetChart() {
      this.chartOption.xAxis.data = [];
      this.chartOption.series = [];
    },
  },
};
</script>

<style scoped>
.right_bottom {
  box-sizing: border-box;
  padding: 0 20px;
  height: 260px;
}
.chart {
  width: 100%;
  height: 100%;
}
</style>
